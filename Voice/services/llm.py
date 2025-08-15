import os
import google.generativeai as genai
from .utils import FALLBACK_TEXT, structured_error

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def query_gemini(prompt: str) -> str:
    """Send text prompt to Gemini API and get response."""
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(prompt)
        return response.text.strip() if response and response.text else FALLBACK_TEXT
    except Exception as e:
        print(f"[LLM ERROR] {e}")
        return structured_error(e, FALLBACK_TEXT)
