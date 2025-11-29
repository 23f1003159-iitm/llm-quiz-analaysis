import asyncio
import json
import base64
import os
import shutil
import httpx
import time
import re
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright

from app.llm import ask_llm
from app.executor import execute_generated_code
from app.scraper import SmartScraper
from app.logger import MissionLogger
from app.prompts import (
    PLANNER_SYSTEM_ROLE, CODER_SYSTEM_ROLE,
    generate_planning_prompt, generate_coding_prompt, fix_json_prompt
)

# CONFIG: Models to use (in order of preference for retries)
MODELS = ["openai/gpt-4.1-nano", "openai/gpt-4.1-nano", "openai/gpt-4.1-nano"]
PLANNER_MODEL = "openai/gpt-4.1-nano"  # More reliable than Gemini for structured output

DOWNLOAD_DIR = "downloads"


def clean_code_output(code: str) -> str:
    """Extract clean Python code from LLM output"""
    # Remove markdown code blocks
    code = re.sub(r'^```python\s*', '', code, flags=re.MULTILINE)
    code = re.sub(r'^```\s*$', '', code, flags=re.MULTILINE)
    code = code.strip()
    
    # If the response starts with text explanation, try to extract code
    if not code.startswith(('import ', 'from ', '#', 'def ', 'class ', 'solution', '\n')):
        # Try to find code block in the response
        match = re.search(r'```python\s*(.*?)```', code, re.DOTALL)
        if match:
            code = match.group(1).strip()
        else:
            # Try to find lines that look like code
            lines = code.split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                if line.strip().startswith(('import ', 'from ', '#', 'def ', 'class ', 'solution')):
                    in_code = True
                if in_code:
                    code_lines.append(line)
            if code_lines:
                code = '\n'.join(code_lines)
    
    return code


def parse_json_safely(raw_text: str) -> dict:
    """Parse JSON from LLM output, handling various formats"""
    # Clean the text
    text = raw_text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from text
    json_patterns = [
        r'\{[^{}]*\}',  # Simple object
        r'\{.*?\}',      # Any object (greedy)
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    return {}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def safe_goto(page, url):
    """Navigate to URL with retry logic"""
    print(f"  🌐 Navigating to: {url}")
    await page.goto(url, timeout=45000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass


async def process_quiz_task(email: str, secret: str, start_url: str):
    """Main quiz processing loop"""
    logger = MissionLogger(task_id=start_url)
    logger.log_step("START", {"url": start_url, "email": email})

    # Clean downloads directory
    if os.path.exists(DOWNLOAD_DIR):
        shutil.rmtree(DOWNLOAD_DIR)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--mute-audio"])
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        scraper = SmartScraper(page)
        await scraper.setup()
        
        current_url = start_url
        global_start_time = time.time()
        questions_solved = 0
        
        while current_url:
            elapsed = time.time() - global_start_time
            if elapsed > 170:  # Leave margin before 3-minute deadline
                print(f"⏰ Time limit approaching ({elapsed:.0f}s). Stopping.")
                break

            server_resp = {}  # Initialize to avoid unbound variable error
            
            try:
                print(f"\n{'='*60}")
                print(f"🚀 Question #{questions_solved + 1}: {current_url}")
                print(f"⏱️  Elapsed: {elapsed:.0f}s")
                print(f"{'='*60}")
                
                await safe_goto(page, current_url)
                
                # Wait for JavaScript rendering
                print("  ⏳ Waiting for JavaScript rendering...")
                await asyncio.sleep(3)
                
                # Scroll to trigger lazy loading
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)
                except:
                    pass

                # Click any download links to trigger downloads
                try:
                    download_links = await page.query_selector_all('a[href*="download"], a[download]')
                    for link in download_links[:3]:  # Max 3 downloads
                        try:
                            async with page.expect_download(timeout=5000) as download_info:
                                await link.click()
                            download = await download_info.value
                            path = os.path.join(DOWNLOAD_DIR, download.suggested_filename)
                            await download.save_as(path)
                            print(f"  📥 Downloaded: {download.suggested_filename}")
                        except:
                            pass
                except:
                    pass

                # A. OBSERVE - Get page context
                page_data = await scraper.get_page_context()
                print(f"  👀 Page text: {len(page_data['text'])} chars")
                print(f"  📎 Files: {page_data['downloaded_files']}")
                print(f"  🔗 Links: {len(page_data['links'])}")
                
                # Take screenshot for vision models
                screenshot_bytes = await page.screenshot(full_page=True)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                
                logger.log_step("OBSERVATION", {
                    "files": page_data['downloaded_files'],
                    "links_count": len(page_data['links']),
                    "text_length": len(page_data['text'])
                }, screenshot_b64)

                # B. STRATEGIZE - Plan the approach
                plan_prompt = generate_planning_prompt(
                    page_data['text'], 
                    page_data['downloaded_files'], 
                    page_data['links']
                )
                
                plan_raw = await ask_llm(
                    plan_prompt, 
                    image_base64=screenshot_b64,
                    system_role=PLANNER_SYSTEM_ROLE, 
                    model=PLANNER_MODEL
                )
                
                # Parse plan
                plan = parse_json_safely(plan_raw)
                
                # Validate and fill defaults
                if not plan.get("question"):
                    # Extract question from page text
                    text = page_data['text'][:2000]
                    plan["question"] = text if text else "Extract the requested information from the page"
                
                if not plan.get("submit_url"):
                    # Try to find submit URL in page text
                    submit_match = re.search(r'https?://[^\s<>"]+/submit[^\s<>"]*', page_data['text'])
                    if submit_match:
                        plan["submit_url"] = submit_match.group(0)
                    else:
                        # Look for any POST endpoint mentioned
                        post_match = re.search(r'https?://[^\s<>"]+', page_data['text'])
                        plan["submit_url"] = post_match.group(0) if post_match else current_url
                
                if not plan.get("format_hint"):
                    plan["format_hint"] = "auto"

                logger.log_step("PLANNING", plan)
                print(f"  📋 Task: {plan['question'][:100]}...")
                print(f"  📤 Submit URL: {plan['submit_url']}")
                print(f"  📝 Format: {plan.get('format_hint')}")

                # C. EXECUTE - Generate and run code
                answer = None
                last_error = ""
                submission_feedback = ""
                
                for attempt in range(3):
                    current_model = MODELS[attempt]
                    print(f"\n  🔄 Attempt {attempt + 1}/3 with {current_model}")
                    
                    # Generate code
                    code_prompt = generate_coding_prompt(
                        task=plan['question'],
                        files=page_data['downloaded_files'],
                        links=page_data['links'],
                        format_hint=plan.get('format_hint', 'auto'),
                        previous_error=last_error,
                        server_feedback=submission_feedback
                    )

                    code_raw = await ask_llm(
                        code_prompt, 
                        system_role=CODER_SYSTEM_ROLE, 
                        model=current_model
                    )
                    
                    # Clean and extract code
                    code = clean_code_output(code_raw)
                    
                    # Execute code
                    result_pkg = execute_generated_code(code)
                    logger.log_step(f"EXEC_{attempt+1}_{current_model}", {
                        "success": result_pkg["success"],
                        "result": str(result_pkg["result"])[:500] if result_pkg["result"] else None,
                        "error": result_pkg["error"][:500] if result_pkg["error"] else None
                    })
                    
                    if result_pkg["success"]:
                        answer = result_pkg["result"]
                        
                        # Validate answer
                        if answer is None:
                            print(f"    ⚠️ Answer is None")
                            last_error = "Code executed but solution was None"
                            continue
                        
                        if isinstance(answer, dict) and "error" in answer:
                            print(f"    ⚠️ Answer contains error: {answer}")
                            last_error = f"Solution returned error dict: {answer}"
                            continue

                        # Unwrap nested answer
                        if isinstance(answer, dict) and "answer" in answer and len(answer) == 1:
                            answer = answer["answer"]
                            
                        if isinstance(answer, str) and "error" in answer.lower() and len(answer) < 100:
                            print(f"    ⚠️ Answer looks like error: {answer}")
                            last_error = f"Solution returned error string: {answer}"
                            continue

                        print(f"    💡 Answer: {str(answer)[:200]}...")
                        
                        # D. SUBMIT
                        payload = {
                            "email": email,
                            "secret": secret,
                            "url": current_url,
                            "answer": answer
                        }
                        
                        print(f"    📤 Submitting to {plan['submit_url']}...")
                        async with httpx.AsyncClient() as client:
                            try:
                                resp = await client.post(
                                    plan['submit_url'], 
                                    json=payload, 
                                    timeout=20.0
                                )
                                server_resp = resp.json()
                            except Exception as e:
                                print(f"    ❌ Submission error: {e}")
                                server_resp = {"error": str(e)}
                                last_error = f"Submission failed: {e}"
                                continue

                        logger.log_step("SUBMISSION", server_resp)
                        print(f"    📬 Response: {server_resp}")

                        if server_resp.get("correct") is True:
                            print("    ✅ CORRECT!")
                            questions_solved += 1
                            current_url = server_resp.get("url")
                            break
                        else:
                            reason = server_resp.get("reason", "Incorrect answer")
                            print(f"    ❌ Wrong: {reason}")
                            
                            # Check if we should skip to next URL
                            if server_resp.get("url"):
                                print(f"    ⏩ Skipping to next: {server_resp['url']}")
                                current_url = server_resp.get("url")
                                break
                            else:
                                submission_feedback = reason
                    else:
                        error_msg = result_pkg['error'][:200] if result_pkg['error'] else "Unknown error"
                        print(f"    ⚠️ Code error: {error_msg}")
                        last_error = result_pkg['error'] or "Code execution failed"
                else:
                    # All attempts failed
                    if not server_resp.get("correct") and not server_resp.get("url"):
                        print("  ⛔ All attempts failed. Stopping.")
                        current_url = None

            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                logger.error(f"CRITICAL: {e}\n{error_trace}")
                print(f"  💥 Critical error: {e}")
                # Try to continue with next URL if available
                if server_resp.get("url"):
                    current_url = server_resp.get("url")
                else:
                    current_url = None
        
        # Cleanup
        await browser.close()
        
        print(f"\n{'='*60}")
        print(f"🏁 Mission Complete! Solved {questions_solved} questions.")
        print(f"⏱️  Total time: {time.time() - global_start_time:.0f}s")
        print(f"{'='*60}")
        
        logger.log_step("COMPLETE", {
            "questions_solved": questions_solved,
            "total_time": time.time() - global_start_time
        })