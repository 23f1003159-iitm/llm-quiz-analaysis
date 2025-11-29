import os
import httpx
from dotenv import load_dotenv

load_dotenv()
AIPIPE_TOKEN = os.getenv("AIPIPE_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Whisper API endpoints
AIPIPE_WHISPER_URL = "https://aipipe.org/openrouter/v1/audio/transcriptions"
OPENAI_WHISPER_URL = "https://api.openai.com/v1/audio/transcriptions"


async def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio file using Whisper API.
    
    Tries AIPIPE first, falls back to OpenAI direct API.
    
    Args:
        file_path: Path to the audio file (mp3, wav, m4a, etc.)
    
    Returns:
        Transcribed text or error message
    """
    if not os.path.exists(file_path):
        return f"Error: Audio file not found: {file_path}"
    
    print(f"  🎤 Transcribing: {file_path}")
    
    # Read the audio file
    with open(file_path, "rb") as f:
        audio_data = f.read()
    
    filename = os.path.basename(file_path)
    
    # Try AIPIPE Whisper endpoint first
    if AIPIPE_TOKEN:
        try:
            result = await _transcribe_via_aipipe(audio_data, filename)
            if result and not result.startswith("Error"):
                return result
        except Exception as e:
            print(f"  ⚠️ AIPIPE Whisper failed: {e}")
    
    # Fallback to OpenAI direct
    if OPENAI_API_KEY:
        try:
            result = await _transcribe_via_openai(audio_data, filename)
            if result and not result.startswith("Error"):
                return result
        except Exception as e:
            print(f"  ⚠️ OpenAI Whisper failed: {e}")
    
    return "Error: No working transcription API available"


async def _transcribe_via_aipipe(audio_data: bytes, filename: str) -> str:
    """Transcribe using AIPIPE's Whisper endpoint"""
    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
    }
    
    files = {
        "file": (filename, audio_data),
        "model": (None, "whisper-1"),
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            AIPIPE_WHISPER_URL,
            headers=headers,
            files=files,
            timeout=120.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return data.get("text", "")
        else:
            return f"Error: AIPIPE returned {resp.status_code}"


async def _transcribe_via_openai(audio_data: bytes, filename: str) -> str:
    """Transcribe using OpenAI's Whisper API directly"""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    
    files = {
        "file": (filename, audio_data),
        "model": (None, "whisper-1"),
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            OPENAI_WHISPER_URL,
            headers=headers,
            files=files,
            timeout=120.0
        )
        
        if resp.status_code == 200:
            data = resp.json()
            return data.get("text", "")
        else:
            return f"Error: OpenAI returned {resp.status_code}"