import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = "gemini-2.5-flash-lite"

_last_llm_call_time = 0
_cached_llm_response = None
LLM_COOLDOWN_SECONDS = 30


def generate_llm_reasoning(
    context_text: str,
    scam_type: str,
    confidence: str,
    reasoning_summary: str,
    risk_level: str,
    risk_score: int = 0,
) -> dict:
    global _last_llm_call_time
    global _cached_llm_response

    if risk_score < 80 and risk_level != "HIGH":
        return {
            "llm_enabled": False,
            "llm_summary": "AI explanation skipped because threat level is below the high-risk threshold.",
        }

    current_time = time.time()

    if (
        _cached_llm_response is not None
        and current_time - _last_llm_call_time < LLM_COOLDOWN_SECONDS
    ):
        return {
            "llm_enabled": True,
            "llm_summary": _cached_llm_response,
            "model": MODEL_NAME,
            "cached": True,
        }

    if not GEMINI_API_KEY:
        fallback = (
            f"This appears to be a {scam_type}. Confidence is {confidence}. "
            f"Reasoning: {reasoning_summary}"
        )

        _cached_llm_response = fallback
        _last_llm_call_time = current_time

        return {
            "llm_enabled": False,
            "llm_summary": fallback,
            "note": "GEMINI_API_KEY not found. Using fallback reasoning.",
        }

    prompt = f"""
You are Praesidium, a real-time AI guardian for detecting digital arrest scams.

Analyze the ongoing conversation and provide a concise, victim-safe explanation.

Scam Type: {scam_type}
Current Confidence: {confidence}
Risk Level: {risk_level}
Risk Score: {risk_score}

Rule-Based Reasoning:
{reasoning_summary}

Conversation Context:
{context_text[-3500:]}

Return in this format:
1. Why this is suspicious:
2. Scam tactics detected:
3. Immediate advice to the victim:

Keep it short, calm, and clear. Do not blame the victim.
"""

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
        )

        llm_text = response.text.strip()

        _cached_llm_response = llm_text
        _last_llm_call_time = current_time

        return {
            "llm_enabled": True,
            "llm_summary": llm_text,
            "model": MODEL_NAME,
            "cached": False,
        }

    except Exception as e:
        fallback = (
            f"This appears to be a {scam_type}. Confidence is {confidence}. "
            f"Reasoning: {reasoning_summary}"
        )

        _cached_llm_response = fallback
        _last_llm_call_time = current_time

        return {
            "llm_enabled": False,
            "llm_summary": fallback,
            "error": str(e),
        }