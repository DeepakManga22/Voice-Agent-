from fastapi import FastAPI, Form, Request, UploadFile, File, Path
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import requests
import os
import shutil
import time

# Google Gemini API
import google.generativeai as genai

# Load environment variables
load_dotenv()

app = FastAPI()

# Mount static and uploads dirs
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Ensure uploads folder exists
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Load API keys
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Constants for fallback
FALLBACK_AUDIO = "/static/fallback.mp3"
FALLBACK_TEXT = "I'm having trouble connecting right now."

# Key checks (fail early in dev)
if not GEMINI_API_KEY:
    print("⚠ Warning: GEMINI_API_KEY not found, LLM will always use fallback.")
if not ASSEMBLYAI_API_KEY:
    print("⚠ Warning: ASSEMBLYAI_API_KEY not found, STT will always use fallback.")
if not MURF_API_KEY:
    print("⚠ Warning: MURF_API_KEY not found, TTS will always use fallback.")

# AssemblyAI headers
ASSEMBLYAI_HEADERS = {"authorization": ASSEMBLYAI_API_KEY} if ASSEMBLYAI_API_KEY else {}

# Gemini config
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Chat history store
CHAT_HISTORY = {}

# ---------- Helper Functions ----------
def structured_error(service: str, err: Exception, fallback_audio=True):
    """Return a structured error with optional fallback audio."""
    return {
        "error": f"{service}_failure",
        "message": FALLBACK_TEXT,
        "details": str(err),
        "audio_url": FALLBACK_AUDIO if fallback_audio else None
    }

def upload_file_to_assemblyai(file_path: str) -> str:
    with open(file_path, "rb") as f:
        response = requests.post(
            "https://api.assemblyai.com/v2/upload", 
            headers=ASSEMBLYAI_HEADERS, 
            data=f
        )
    response.raise_for_status()
    return response.json()["upload_url"]

def request_transcription(audio_url: str) -> str:
    json_payload = {"audio_url": audio_url}
    response = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        json=json_payload, headers=ASSEMBLYAI_HEADERS
    )
    response.raise_for_status()
    return response.json()["id"]

def get_transcription_result(transcript_id: str) -> str:
    polling_endpoint = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"
    while True:
        response = requests.get(polling_endpoint, headers=ASSEMBLYAI_HEADERS)
        response.raise_for_status()
        status = response.json()["status"]
        if status == "completed":
            return response.json()["text"]
        elif status == "error":
            raise Exception("Transcription failed: " + response.json().get("error", "Unknown error"))
        else:
            time.sleep(3)

def generate_tts(text: str, voiceId: str):
    if not MURF_API_KEY:
        raise Exception("Murf API key missing")
    murf_url = "https://api.murf.ai/v1/speech/generate"
    headers = {"Accept": "application/json", "Content-Type": "application/json", "api-key": MURF_API_KEY}
    payload = {"text": text, "voiceId": voiceId, "format": "MP3", "sampleRate": 24000}
    resp = requests.post(murf_url, json=payload, headers=headers)
    resp.raise_for_status()
    return resp.json().get("audioFile", FALLBACK_AUDIO)

# ---------- Endpoints ----------
@app.post("/tts")
async def tts(text: str = Form(...), voiceId: str = Form("en-US-natalie")):
    try:
        audio_url = generate_tts(text, voiceId)
        return {"audio_url": audio_url}
    except Exception as e:
        return structured_error("tts", e)

@app.get("/voices")
async def get_voices():
    if not MURF_API_KEY:
        return structured_error("voices", Exception("Murf API key not configured."))
    try:
        url = "https://api.murf.ai/v1/speech/voices"
        headers = {"Accept": "application/json", "api-key": MURF_API_KEY}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return structured_error("voices", e, fallback_audio=False)

@app.post("/upload-audio")
async def upload_audio(audio_file: UploadFile = File(...)):
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        file_size = os.path.getsize(file_path)
        file_url = f"/uploads/{audio_file.filename}"
        return {"filename": audio_file.filename,"content_type": audio_file.content_type,"size": file_size,"file_url": file_url}
    except Exception as e:
        return structured_error("upload_audio", e, fallback_audio=False)
    finally:
        await audio_file.close()

@app.post("/transcribe_assemblyai")
async def transcribe_assemblyai(audio_file: UploadFile = File(...)):
    if not ASSEMBLYAI_API_KEY:
        return structured_error("stt", Exception("AssemblyAI API key not configured."))
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await audio_file.read())
        upload_url = upload_file_to_assemblyai(file_path)
        transcript_id = request_transcription(upload_url)
        text = get_transcription_result(transcript_id)
        return {"transcription": text}
    except Exception as e:
        return structured_error("stt", e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/tts/echo")
async def echo_tts(audio_file: UploadFile = File(...), voiceId: str = Form("en-US-natalie")):
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    transcription = None
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await audio_file.read())
        try:
            upload_url = upload_file_to_assemblyai(file_path)
            transcript_id = request_transcription(upload_url)
            transcription = get_transcription_result(transcript_id)
        except Exception as se:
            return structured_error("stt", se)
        try:
            audio_url = generate_tts(transcription, voiceId)
        except Exception:
            audio_url = FALLBACK_AUDIO
        return {"audio_url": audio_url, "transcription": transcription}
    except Exception as e:
        return structured_error("echo_tts", e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/llm/query")
async def llm_query(audio_file: UploadFile = File(...), voiceId: str = Form("en-US-natalie")):
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    transcription = llm_text = None
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await audio_file.read())
        # STT
        try:
            upload_url = upload_file_to_assemblyai(file_path)
            transcript_id = request_transcription(upload_url)
            transcription = get_transcription_result(transcript_id)
        except Exception as se:
            return structured_error("stt", se)
        # LLM
        try:
            if GEMINI_API_KEY:
                model = genai.GenerativeModel("gemini-1.5-flash")
                llm_text = model.generate_content(transcription).text
            else:
                raise Exception("Gemini API key not configured")
        except Exception:
            llm_text = FALLBACK_TEXT
        # TTS
        try:
            audio_url = generate_tts(llm_text, voiceId)
        except Exception:
            audio_url = FALLBACK_AUDIO
        return {"transcription": transcription,"llm_response": llm_text,"audio_url": audio_url}
    except Exception as e:
        return structured_error("llm_query", e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str = Path(...),audio_file: UploadFile = File(...),voiceId: str = Form("en-US-natalie")):
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    user_message = llm_text = None
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await audio_file.read())
        # STT
        try:
            upload_url = upload_file_to_assemblyai(file_path)
            transcript_id = request_transcription(upload_url)
            user_message = get_transcription_result(transcript_id)
        except Exception as se:
            return structured_error("stt", se)
        # Store to history
        history = CHAT_HISTORY.setdefault(session_id, [])
        history.append({"role": "user", "content": user_message})
        messages = [f"{h['role'].capitalize()}: {h['content']}" for h in history]
        full_prompt = "\n".join(messages)
        # LLM
        try:
            if GEMINI_API_KEY:
                model = genai.GenerativeModel("gemini-1.5-flash")
                llm_text = model.generate_content(full_prompt).text
            else:
                raise Exception("Gemini API key not configured")
        except Exception:
            llm_text = FALLBACK_TEXT
        history.append({"role": "assistant", "content": llm_text})
        # TTS
        try:
            audio_url = generate_tts(llm_text, voiceId)
        except Exception:
            audio_url = FALLBACK_AUDIO
        return {"session_id": session_id,"audio_url": audio_url,"transcription": user_message,"llm_response": llm_text}
    except Exception as e:
        return structured_error("agent_chat", e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})