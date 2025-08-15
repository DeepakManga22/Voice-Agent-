import os
import requests
from .utils import structured_error, FALLBACK_AUDIO

MURF_API_KEY = os.getenv("MURF_API_KEY")
BASE_URL = "https://api.murf.ai/v1"

def generate_tts(text: str) -> bytes:
    """Convert text to speech using Murf API and return audio bytes."""
    try:
        headers = {
            "Authorization": f"Bearer {MURF_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "voice": "en-US-morgan",  # Example voice
            "text": text
        }
        response = requests.post(f"{BASE_URL}/speech", headers=headers, json=payload)
        response.raise_for_status()
        return response.content if response.content else FALLBACK_AUDIO
    except Exception as e:
        print(f"[TTS ERROR] {e}")
        return structured_error(e, FALLBACK_AUDIO)
