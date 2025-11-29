import os
import httpx
import json
from dotenv import load_dotenv

load_dotenv()
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Endpoints
AIPIPE_URL = "https://aipipe.org/openrouter/v1/chat/completions"
GEMINI_URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

async def ask_llm(prompt_text: str, image_base64: str = None, system_role: str = "Expert Coder", model: str = "openai/gpt-5-nano"):
    # ROUTE 1: GOOGLE GEMINI
    if "gemini" in model.lower():
        if not GEMINI_API_KEY: return "Error: GEMINI_API_KEY missing"
        clean_model = model.replace("google/", "")
        url = f"{GEMINI_URL_BASE}/{clean_model}:generateContent?key={GEMINI_API_KEY}"
        parts = [{"text": f"SYSTEM: {system_role}\n\nUSER: {prompt_text}"}]
        if image_base64: parts.append({"inline_data": {"mime_type": "image/png", "data": image_base64}})
        payload = {"contents": [{"parts": parts}],"generationConfig": {"temperature": 0.1}}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload, timeout=60.0)
                return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e: return f"Gemini Error: {e}"
    
    # ROUTE 2: AI PIPE
    else:
        if not AIPIPE_TOKEN: return "Error: AIPIPE_TOKEN missing"
        headers = {"Authorization": f"Bearer {AIPIPE_TOKEN}", "Content-Type": "application/json", "HTTP-Referer": "https://quiz.com"}
        content = [{"type": "text", "text": prompt_text}]
        if image_base64: content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}})
        payload = {"model": model, "messages": [{"role": "system", "content": system_role}, {"role": "user", "content": content}], "temperature": 0.1}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(AIPIPE_URL, headers=headers, json=payload, timeout=90.0)
                return resp.json()["choices"][0]["message"]["content"]
            except Exception as e: return f"AI Pipe Error: {e}"
