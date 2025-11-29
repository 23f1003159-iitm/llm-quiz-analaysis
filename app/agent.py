import asyncio
import json
import base64
import os
import shutil
import httpx
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from playwright.async_api import async_playwright

from app.llm import ask_llm
from app.executor import execute_generated_code
from app.scraper import SmartScraper
from app.logger import MissionLogger
# IMPORT THE NEW PROMPTS
from app.prompts import (
    PLANNER_SYSTEM_ROLE, CODER_SYSTEM_ROLE,
    generate_planning_prompt, generate_coding_prompt, fix_json_prompt
)

# CONFIG: All using GPT-5-nano for consistency and reliability
MODELS = ["openai/gpt-5-nano", "openai/gpt-5-nano", "openai/gpt-5-nano"]

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def safe_goto(page, url):
    print(f"Trying to visit: {url}")
    await page.goto(url, timeout=45000)
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except:
        pass

async def process_quiz_task(email: str, secret: str, start_url: str):
    logger = MissionLogger(task_id=start_url)
    logger.log_step("START", {"url": start_url})

    if os.path.exists("downloads"): shutil.rmtree("downloads")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--mute-audio"])
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        
        scraper = SmartScraper(page)
        await scraper.setup()
        
        current_url = start_url
        global_start_time = time.time()
        
        while current_url:
            if time.time() - global_start_time > 175:
                print("⏰ Time Limit Exceeded. Stopping.")
                break

            try:
                print(f"\n🚀 Mission Level: {current_url}")
                await safe_goto(page, current_url)
                
                print("⏳ Waiting 5s for JavaScript rendering...")
                await asyncio.sleep(5) 
                
                try:
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                except: pass

                # A. OBSERVE
                page_data = await scraper.get_page_context()
                print(f"👀 Scraped Text: {len(page_data['text'])} chars | Links: {len(page_data['links'])}")
                
                screenshot_bytes = await page.screenshot(full_page=True)
                screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
                
                logger.log_step("OBSERVATION", {"files": page_data['downloaded_files']}, screenshot_b64)

                # B. STRATEGIZE
                # Try Gemini Flash for Planning (Best Reader), fallback to GPT-5-nano
                plan_prompt_text = generate_planning_prompt(page_data['text'], page_data['downloaded_files'], page_data['links'])
                
                plan_raw = await ask_llm(plan_prompt_text, screenshot_b64, PLANNER_SYSTEM_ROLE, model="gemini-1.5-flash")
                
                # Fallback to GPT if Gemini errors
                if "Gemini Error" in plan_raw or "Error:" in plan_raw:
                    print(f"⚠️ Gemini failed: {plan_raw[:100]}. Falling back to GPT-5-nano...")
                    plan_raw = await ask_llm(plan_prompt_text, screenshot_b64, PLANNER_SYSTEM_ROLE, model="openai/gpt-5-nano")
                
                clean_plan = plan_raw.replace("```json", "").replace("```", "").strip()
                try:
                    plan = json.loads(clean_plan)
                except Exception:
                    print("⚠️ Plan JSON Error. Fixing...")
                    fix_prompt = fix_json_prompt(clean_plan)
                    plan_raw = await ask_llm(fix_prompt, system_role="JSON Fixer", model="openai/gpt-5-nano")
                    try:
                        plan = json.loads(plan_raw.replace("```json", "").replace("```", "").strip())
                    except Exception:
                        plan = None

                if not isinstance(plan, dict):
                    plan = {}

                if not plan.get("question"):
                    fallback_question = page_data['text'][:500].strip() or "Read the page and extract the requested answer."
                    plan["question"] = fallback_question

                if not plan.get("submit_url"):
                    plan["submit_url"] = current_url

                if not plan.get("format_hint"):
                    plan["format_hint"] = "string"

                logger.log_step("PLANNING", plan)
                print(f"📋 Question: {plan['question']}")
                print(f"🧠 Format Hint: {plan.get('format_hint')}")

                # C. EXECUTION LOOP
                answer = None
                last_error = ""
                submission_feedback = "" 
                
                for attempt in range(3):
                    current_model = MODELS[attempt]
                    
                    code_prompt_text = generate_coding_prompt(
                        task=plan['question'],
                        files=page_data['downloaded_files'],
                        links=page_data['links'],
                        format_hint=plan.get('format_hint', 'Any'),
                        previous_error=last_error,
                        server_feedback=submission_feedback
                    )

                    code = await ask_llm(code_prompt_text, system_role=CODER_SYSTEM_ROLE, model=current_model)
                    code = code.replace("```python", "").replace("```", "").strip()
                    
                    result_pkg = execute_generated_code(code)
                    logger.log_step(f"EXEC_{attempt+1}_{current_model}", result_pkg)
                    
                    if result_pkg["success"]:
                        answer = result_pkg["result"]
                        
                        # --- STRICT TYPE GUARD ---
                        if isinstance(answer, dict) and "error" in answer:
                            print(f"⚠️ Answer is error dict: {answer}. Treating as Failure.")
                            last_error = f"Agent produced error dict: {answer}"
                            continue

                        if isinstance(answer, dict) and "answer" in answer and len(answer) == 1:
                            answer = answer["answer"]
                            
                        if isinstance(answer, str) and "error" in answer.lower() and len(answer) < 50:
                            print(f"⚠️ Answer is error string: {answer}. Treating as Failure.")
                            last_error = f"Agent returned error string: {answer}"
                            continue

                        print(f"💡 Generated Answer: {answer} (Model: {current_model})")
                        
                        payload = {
                            "email": email,
                            "secret": secret,
                            "url": current_url,
                            "answer": answer
                        }
                        
                        print(f"📤 Submitting to {plan['submit_url']}...")
                        async with httpx.AsyncClient() as client:
                            try:
                                resp = await client.post(plan['submit_url'], json=payload, timeout=15.0)
                                server_resp = resp.json()
                            except Exception as e:
                                server_resp = {"error": str(e)}

                        logger.log_step("SUBMISSION", server_resp)
                        print(f"📬 Server said: {server_resp}")

                        if server_resp.get("correct") is True:
                            print("✅ Correct! Moving to next level...")
                            current_url = server_resp.get("url")
                            break
                        else:
                            if server_resp.get("url"):
                                print("⏩ Wrong, but skipping...")
                                current_url = server_resp.get("url")
                                break
                            else:
                                print(f"❌ Wrong (Model {current_model}). Retrying...")
                                submission_feedback = server_resp.get("reason", "Incorrect answer")
                    else:
                        print(f"⚠️ Code Error (Model {current_model}): {result_pkg['error'][:100]}")
                        last_error = result_pkg['error']
                
                if not server_resp.get("correct") and not server_resp.get("url"):
                    print("⛔ Failed 3 attempts. Stopping.")
                    current_url = None

            except Exception as e:
                logger.error(f"CRITICAL: {e}")
                print(f"💥 Critical: {e}")
                current_url = None
        
        await browser.close()