import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")

# Endpoints
AIPIPE_URL = "https://aipipe.org/openrouter/v1/chat/completions"


async def ask_llm(
    prompt_text: str, 
    image_base64: str = None, 
    system_role: str = "Expert Coder", 
    model: str = "openai/gpt-4.1-nano"
) -> str:
    """
    Send a prompt to the LLM and get a response.
    
    Args:
        prompt_text: The main prompt/question
        image_base64: Optional base64 encoded image for vision models
        system_role: The system prompt defining the AI's role
        model: Model identifier (e.g., "openai/gpt-4.1-nano")
    
    Returns:
        The LLM's response text, or an error message
    """
    if not AIPIPE_TOKEN:
        return "Error: AIPIPE_TOKEN not configured in environment"
    
    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://quiz-solver.app"
    }
    
    # Build content array
    content = [{"type": "text", "text": prompt_text}]
    
    # Add image if provided and model supports vision
    if image_base64:
        content.append({
            "type": "image_url", 
            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
        })
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_role},
            {"role": "user", "content": content}
        ],
        "temperature": 0.1,
        "max_tokens": 4096
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                AIPIPE_URL, 
                headers=headers, 
                json=payload, 
                timeout=120.0
            )
            
            if resp.status_code != 200:
                error_text = resp.text[:500]
                print(f"  ⚠️ LLM API error ({resp.status_code}): {error_text}")
                return f"API Error ({resp.status_code}): {error_text}"
            
            data = resp.json()
            
            # Handle various response formats
            if "choices" in data and len(data["choices"]) > 0:
                message = data["choices"][0].get("message", {})
                content = message.get("content", "")
                if content:
                    return content
                
                # Some models return text directly
                text = data["choices"][0].get("text", "")
                if text:
                    return text
            
            # Handle error responses
            if "error" in data:
                error_msg = data["error"]
                if isinstance(error_msg, dict):
                    error_msg = error_msg.get("message", str(error_msg))
                print(f"  ⚠️ LLM returned error: {error_msg}")
                return f"LLM Error: {error_msg}"
            
            print(f"  ⚠️ Unexpected response format: {str(data)[:200]}")
            return f"Unexpected response: {str(data)[:200]}"
            
        except httpx.TimeoutException:
            print("  ⚠️ LLM request timed out")
            return "Error: Request timed out"
        except json.JSONDecodeError as e:
            print(f"  ⚠️ Failed to parse LLM response: {e}")
            return f"JSON Parse Error: {e}"
        except Exception as e:
            print(f"  ⚠️ LLM request failed: {e}")
            return f"Request Error: {e}"
