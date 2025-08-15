# 🎙 Voice Agent Project – 30 Days of AI Voice Agents

An end-to-end AI-powered conversational voice agent built for the **#30DaysofVoiceAgents** challenge by Murf AI.

The bot listens to your voice, converts it to text (STT), processes it with a Large Language Model (LLM), and responds with Text-to-Speech (TTS) — all in real-time.

---

## 🚀 Features

- **Speech-to-Text (STT):** Converts audio into text using AssemblyAI.
- **LLM Integration:** Uses Google Gemini API for intelligent, context-aware responses.
- **Text-to-Speech (TTS):** Generates natural-sounding voice replies using Murf API or AssemblyAI.
- **Chat History:** Remembers previous messages in a session for more human-like conversation.
- **Error Handling:** Friendly fallback when APIs fail (e.g., “I'm having trouble connecting right now”).
- **Revamped UI:** Clean, minimal interface with an animated record button and automatic audio playback.

---

## 🛠 Technologies Used

### Backend

- Python (FastAPI) — API server  
- Uvicorn  
- dotenv — Manage API keys and configuration

### Frontend

- HTML, CSS, JavaScript  
- Bootstrap — Responsive UI styling  
- Fetch API — Async communication with backend

### Voice APIs

- Google Gemini  
- AssemblyAI  
- Murf  

---

## 📂 Project Structure

Voice-Agent/
│
├── main.py # FastAPI entry point
├── requirements.txt # Python dependencies
├── .env # API keys (do not share)
│
├── services/
│ ├── init.py
│ ├── llm.py # Google Gemini integration
│ ├── stt.py # AssemblyAI integration
│ ├── tts.py # Murf API integration
│ └── utils.py # Helper constants & error handling
│
├── static/
│ └── script.js # UI logic
│
├── templates/
│ └── index.html # Frontend UI
│
└── README.md


---

## ⚙️ Setup & Installation

### 1️⃣ Clone the Repository

git clone https://github.com/your-username/Voice-Agent.git

cd Voice-Agent


### 2️⃣ Create a Virtual Environment

python -m venv venv


Activate it:

- **Windows:**
venv\Scripts\activate

- **Mac/Linux:**
source venv/bin/activate


### 3️⃣ Install Dependencies

pip install -r requirements.txt

text

### 4️⃣ Set Environment Variables

Create a `.env` file in the project root:

GEMINI_API_KEY=your_google_gemini_key

ASSEMBLYAI_API_KEY=your_assemblyai_key

MURF_API_KEY=your_murf_api_key



### 5️⃣ Run the Server

uvicorn main:app --reload



Server will be running at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🌐 API Endpoints

| Method | Endpoint           | Description                            |
|--------|--------------------|------------------------------------|
| POST   | `/llm/query`       | Send text/audio and get AI response |
| POST   | `/stt/transcribe`  | Convert audio to text (AssemblyAI)  |
| POST   | `/tts/speak`       | Convert text to audio (Murf API)    |

---

## 🖼️ Frontend

Located in:

- `templates/index.html`  
- `static/script.js`  

UI includes:

- 🎤 Record voice  
- 📝 Display transcribed text  
- 🔊 Play AI-generated voice  

---

## 📌 Notes

- Keep `.env` private — never commit it to GitHub.  
- Make sure all services are active and API keys are valid.  
- This project is for educational purposes — API usage may incur costs.

---

Happy building!
