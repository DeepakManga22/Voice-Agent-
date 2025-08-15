import os
import requests
from .utils import structured_error, FALLBACK_TEXT

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
BASE_URL = "https://api.assemblyai.com/v2"

def upload_file_to_assemblyai(file_path: str) -> str:
    """Upload audio file to AssemblyAI and return upload URL."""
    try:
        headers = {"authorization": ASSEMBLYAI_API_KEY}
        with open(file_path, "rb") as f:
            response = requests.post(f"{BASE_URL}/upload", headers=headers, data=f)
        response.raise_for_status()
        return response.json()["upload_url"]
    except Exception as e:
        print(f"[STT UPLOAD ERROR] {e}")
        return structured_error(e, None)

def request_transcription(audio_url: str) -> str:
    """Request transcription job from AssemblyAI and return job ID."""
    try:
        headers = {
            "authorization": ASSEMBLYAI_API_KEY,
            "content-type": "application/json"
        }
        json_data = {"audio_url": audio_url}
        response = requests.post(f"{BASE_URL}/transcript", headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()["id"]
    except Exception as e:
        print(f"[STT REQUEST ERROR] {e}")
        return structured_error(e, None)

def get_transcription_result(job_id: str) -> str:
    """Fetch transcription result text."""
    try:
        headers = {"authorization": ASSEMBLYAI_API_KEY}
        response = requests.get(f"{BASE_URL}/transcript/{job_id}", headers=headers)
        response.raise_for_status()
        status = response.json()["status"]

        if status == "completed":
            return response.json()["text"]
        elif status == "error":
            raise Exception(response.json()["error"])
        else:
            return None  # still processing
    except Exception as e:
        print(f"[STT RESULT ERROR] {e}")
        return structured_error(e, FALLBACK_TEXT)
