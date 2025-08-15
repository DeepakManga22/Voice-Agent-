from fastapi import FastAPI, Form, Request, UploadFile, File, Path
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import shutil

# Import everything from services via __init__.py
from services import (
    structured_error,
    FALLBACK_AUDIO,
    FALLBACK_TEXT,
    upload_file_to_assemblyai,
    request_transcription,
    get_transcription_result,
    generate_tts,
    query_gemini
)

app = FastAPI()

# Mount static and uploads dirs
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
templates = Jinja2Templates(directory="templates")

# Ensure uploads folder exists
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Chat history store
CHAT_HISTORY = {}

@app.post("/tts")
async def tts(text: str = Form(...), voiceId: str = Form("en-US-natalie")):
    try:
        audio_url = generate_tts(text, voiceId)
        return {"audio_url": audio_url}
    except Exception as e:
        return structured_error("tts", e)

@app.post("/transcribe")
async def transcribe(audio_file: UploadFile = File(...)):
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    try:
        with open(file_path, "wb") as f:
            f.write(await audio_file.read())
        upload_url = upload_file_to_assemblyai(file_path)
        transcript_id = request_transcription(upload_url)
        text = get_transcription_result(transcript_id)
        return {"transcription": text}
    except Exception as e:
        return structured_error("stt", e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/llm/query")
async def llm_query(audio_file: UploadFile = File(...), voiceId: str = Form("en-US-natalie")):
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    transcription = llm_text = None
    try:
        with open(file_path, "wb") as f:
            f.write(await audio_file.read())
        upload_url = upload_file_to_assemblyai(file_path)
        transcript_id = request_transcription(upload_url)
        transcription = get_transcription_result(transcript_id)
        try:
            llm_text = query_gemini(transcription)
        except Exception:
            llm_text = FALLBACK_TEXT
        try:
            audio_url = generate_tts(llm_text, voiceId)
        except Exception:
            audio_url = FALLBACK_AUDIO
        return {"transcription": transcription, "llm_response": llm_text, "audio_url": audio_url}
    except Exception as e:
        return structured_error("llm_query", e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str = Path(...),
                     audio_file: UploadFile = File(...),
                     voiceId: str = Form("en-US-natalie")):
    file_path = os.path.join(UPLOADS_DIR, audio_file.filename)
    user_message = llm_text = None
    try:
        with open(file_path, "wb") as f:
            f.write(await audio_file.read())
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
            llm_text = query_gemini(full_prompt)
        except Exception:
            llm_text = FALLBACK_TEXT
        history.append({"role": "assistant", "content": llm_text})
        # TTS
        try:
            audio_url = generate_tts(llm_text, voiceId)
        except Exception:
            audio_url = FALLBACK_AUDIO
        return {
            "session_id": session_id,
            "audio_url": audio_url,
            "transcription": user_message,
            "llm_response": llm_text
        }
    except Exception as e:
        return structured_error("agent_chat", e)
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
