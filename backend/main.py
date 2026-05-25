import os
import tempfile
from backend.services.scam_reasoning_engine import generate_scam_reasoning
from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
from backend.services.live_guardian_advisor import generate_live_guidance
from backend.services.fraud_analyzer import analyze_text
from backend.services.transcription_service import transcribe_audio
from backend.services.conversation_memory import ConversationMemory
from backend.services.multimodal_risk_engine import fuse_multimodal_risk
from backend.services.llm_reasoning_service import generate_llm_reasoning
from backend.services.victim_state_analyzer import analyze_victim_state


app = FastAPI(title="Praesidium Fraud Detection Backend")

conversation_memory = ConversationMemory()


class AnalyzeRequest(BaseModel):
    text: str
    speaker: str = "unknown"


@app.get("/")
def root():
    return {"message": "Praesidium Backend is running"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    result = analyze_text(request.text, request.speaker)
    return result


@app.post("/transcribe-analyze")
async def transcribe_and_analyze(
    file: UploadFile = File(...),
    speaker: str = Form("unknown"),
    face_detected: bool = Form(False),
    visual_stress_level: str = Form("UNKNOWN"),
    attention_status: str = Form("UNKNOWN"),
):
    suffix = os.path.splitext(file.filename)[-1] or ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
        temp_audio.write(await file.read())
        temp_audio_path = temp_audio.name

    try:
        transcript = transcribe_audio(temp_audio_path)

        if transcript:
            conversation_memory.add_turn(speaker, transcript)

        full_context = conversation_memory.get_context_text()

        latest_analysis = analyze_text(transcript, speaker)
        context_analysis = analyze_text(full_context, speaker)

        conversation_memory.update_risk(context_analysis)

        memory_state = conversation_memory.get_state()
        victim_text = " ".join([
            turn["text"]
            for turn in memory_state["turns"]
            if turn["speaker"].lower() == "victim"
        ])
        victim_support = analyze_victim_state(
            victim_text=victim_text,
            visual_stress_level=visual_stress_level,
            attention_status=attention_status,
            face_detected=face_detected,
        )

        speech_risk_score = memory_state["cumulative_risk_score"]
        speech_risk_level = memory_state["cumulative_risk_level"]
        detected_patterns = memory_state["all_detected_patterns"]

        fused_result = fuse_multimodal_risk(
            speech_risk_score=speech_risk_score,
            speech_risk_level=speech_risk_level,
            detected_patterns=detected_patterns,
            visual_stress_level=visual_stress_level,
            attention_status=attention_status,
            face_detected=face_detected,
        )
        scam_reasoning = generate_scam_reasoning(
             context_text=memory_state["context_text"],
             detected_patterns=detected_patterns,
             fused_risk_score=fused_result["fused_risk_score"],
             fused_risk_level=fused_result["fused_risk_level"],
             visual_context=fused_result["visual_context"],
        )
        live_guidance = generate_live_guidance(
            fused_risk_level=fused_result["fused_risk_level"],
            fused_risk_score=fused_result["fused_risk_score"],
            scam_type=scam_reasoning.get("scam_type", "Unknown"),
            detected_patterns=detected_patterns,
            context_text=memory_state["context_text"],
        )
        llm_reasoning = generate_llm_reasoning(
             context_text=memory_state["context_text"],
             scam_type=scam_reasoning["scam_type"],
             confidence=scam_reasoning["confidence"],
             reasoning_summary=scam_reasoning["reasoning_summary"],
              risk_level=fused_result["fused_risk_level"],
              risk_score=fused_result["fused_risk_score"],
        )


        return {
            "speaker": speaker,
            "transcript": transcript,
            "latest_analysis": latest_analysis,
            "analysis": {
                "risk_score": speech_risk_score,
                "risk_level": speech_risk_level,
                "detected_patterns": detected_patterns,
                "recommended_action": get_recommended_action(speech_risk_level),
                "context_text": memory_state["context_text"],
                "turns": memory_state["turns"],
            },
            "fused_analysis": fused_result,
            "scam_reasoning": scam_reasoning,
            "live_guidance": live_guidance,
            "llm_reasoning": llm_reasoning,
            "victim_support": victim_support,
        }

    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)


@app.post("/reset-conversation")
def reset_conversation():
    conversation_memory.reset()
    return {"message": "Conversation memory reset successfully"}


def get_recommended_action(risk_level: str) -> str:
    if risk_level == "HIGH":
        return (
            "High-risk digital arrest scam detected. Do not share OTP, bank details, "
            "or transfer money. Disconnect the call immediately and report to 1930."
        )

    if risk_level == "MEDIUM":
        return (
            "Suspicious conversation pattern detected. Stay cautious and verify "
            "through official channels before taking any action."
        )

    return "No major scam pattern detected yet. Continue monitoring."