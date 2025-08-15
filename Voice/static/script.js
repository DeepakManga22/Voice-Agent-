// ====== DOM Elements ======
const textInput = document.getElementById("textInput");
const generateBtn = document.getElementById("generateBtn");
const audioPlayer = document.getElementById("audioPlayer");
const errorDisplay = document.getElementById("errorDisplay");

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const uploadInfo = document.getElementById("uploadInfo");
const uploadedAudioPlayer = document.getElementById("uploadedAudioPlayer");

const transcriptionStatus = document.getElementById("transcriptionStatus");
const transcriptionContainer = document.getElementById("transcriptionContainer");
const transcriptionResult = document.getElementById("transcriptionResult");

const llmInput = document.getElementById("llmInput");
const llmBtn = document.getElementById("llmBtn");
const llmOutput = document.getElementById("llmOutput");

// Local fallback audio
const LOCAL_FALLBACK_AUDIO = "/static/fallback.mp3";

// ========== Chat Session Management ============
function getOrCreateSessionId() {
  const url = new URL(window.location.href);
  let sessionId = url.searchParams.get("session_id");
  if (!sessionId) {
    sessionId = Math.random().toString(36).substr(2, 10);
    url.searchParams.set("session_id", sessionId);
    window.history.replaceState({}, "", url.toString());
  }
  return sessionId;
}
const sessionId = getOrCreateSessionId();

// ====== Audio Recording Logic ======
let mediaRecorder;
let audioChunks = [];

function startRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    alert("Audio recording is not supported by your browser.");
    return;
  }
  navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.push(event.data);
    };

    mediaRecorder.onstop = onAudioRecorded;

    mediaRecorder.start();
    startBtn.disabled = true;
    stopBtn.disabled = false;
    uploadInfo.textContent = "Recording... Speak now!";
    uploadInfo.hidden = false;
  }).catch((err) => {
    alert("Could not start audio recording: " + err.message);
  });
}

function stopRecording() {
  if (mediaRecorder) {
    mediaRecorder.stop();
  }
}

async function onAudioRecorded() {
  const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
  const filename = `recording_${Date.now()}.webm`;

  startBtn.disabled = false;
  stopBtn.disabled = true;

  uploadInfo.hidden = false;
  uploadInfo.textContent = "Processing...";

  transcriptionStatus.hidden = true;
  transcriptionContainer.hidden = true;
  uploadedAudioPlayer.hidden = true;

  const formData = new FormData();
  formData.append("audio_file", audioBlob, filename);
  formData.append("voiceId", "en-US-natalie");

  try {
    const response = await fetch(`/agent/chat/${sessionId}`, { method: "POST", body: formData });
    const data = await response.json();

    if (response.ok && !data.error && data.audio_url) {
      uploadedAudioPlayer.src = data.audio_url || LOCAL_FALLBACK_AUDIO;
      uploadedAudioPlayer.hidden = false;
      uploadedAudioPlayer.play().catch(() => {});
      uploadInfo.textContent = "Assistant is replying...";

      if (data.llm_response) {
        transcriptionResult.textContent = data.llm_response;
        transcriptionStatus.hidden = false;
        transcriptionContainer.hidden = false;
      }

      uploadedAudioPlayer.onended = () => {
        setTimeout(() => startRecording(), 500);
      };
    } else {
      handleErrorResponse(data, uploadInfo);
    }
  } catch (err) {
    handleErrorResponse({ error: err.message }, uploadInfo);
  }
}

// ====== TTS (manual) ======
async function generateTTS() {
  const text = textInput.value.trim();
  errorDisplay.textContent = "";
  audioPlayer.hidden = true;
  audioPlayer.src = "";

  if (!text) {
    errorDisplay.textContent = "Please enter some text to generate voice.";
    return;
  }

  generateBtn.disabled = true;
  generateBtn.textContent = "Generating...";

  try {
    const formData = new FormData();
    formData.append("text", text);
    formData.append("voiceId", "en-US-natalie");

    const response = await fetch("/tts", { method: "POST", body: formData });
    const data = await response.json();

    if (response.ok && !data.error && data.audio_url) {
      audioPlayer.src = data.audio_url || LOCAL_FALLBACK_AUDIO;
      audioPlayer.hidden = false;
      audioPlayer.play().catch(() => {});
    } else {
      handleErrorResponse(data, errorDisplay);
    }
  } catch (err) {
    handleErrorResponse({ error: err.message }, errorDisplay);
  } finally {
    generateBtn.disabled = false;
    generateBtn.textContent = "Generate Voice";
  }
}

// ====== LLM Text Query ======
async function sendToLLM() {
  const text = llmInput.value.trim();
  llmOutput.textContent = "";
  if (!text) {
    llmOutput.textContent = "Please enter some text.";
    return;
  }

  llmBtn.disabled = true;
  llmBtn.textContent = "Thinking...";

  try {
    const formData = new FormData();
    formData.append("text", text);

    const response = await fetch("/llm/query", { method: "POST", body: formData });
    const data = await response.json();

    if (response.ok && !data.error && data.llm_response) {
      llmOutput.textContent = data.llm_response;
    } else {
      handleErrorResponse(data, llmOutput);
    }
  } catch (err) {
    handleErrorResponse({ error: err.message }, llmOutput);
  } finally {
    llmBtn.disabled = false;
    llmBtn.textContent = "Ask AI";
  }
}

// ====== Error & Fallback Helpers ======
function handleErrorResponse(data, displayElement) {
  if (data?.audio_url) {
    playAudio(data.audio_url);
  } else {
    playFallbackAudio();
  }
  if (displayElement) {
    displayElement.textContent = data?.error || "Operation failed.";
  }
}

function playAudio(url) {
  const audio = new Audio(url);
  audio.play().catch(() => {});
}

function playFallbackAudio() {
  const fallbackAudio = new Audio(LOCAL_FALLBACK_AUDIO);
  fallbackAudio.play().catch(() => {});
}

// ====== Hook up buttons ======
if (startBtn) startBtn.addEventListener("click", startRecording);
if (stopBtn) stopBtn.addEventListener("click", stopRecording);
if (generateBtn) generateBtn.addEventListener("click", generateTTS);
if (llmBtn) llmBtn.addEventListener("click", sendToLLM);
