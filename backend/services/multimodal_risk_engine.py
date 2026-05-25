def fuse_multimodal_risk(
    speech_risk_score: int,
    speech_risk_level: str,
    detected_patterns: list,
    visual_stress_level: str = "UNKNOWN",
    attention_status: str = "UNKNOWN",
    face_detected: bool = False,
) -> dict:

    fused_score = speech_risk_score
    fusion_reasons = []

    # Speech evidence
    if speech_risk_score >= 70:
        fusion_reasons.append("High-risk scam language detected in conversation.")
    elif speech_risk_score >= 35:
        fusion_reasons.append("Suspicious scam-like conversation pattern detected.")

    # Visual stress evidence
    if face_detected:
        if visual_stress_level == "HIGH":
            fused_score += 15
            fusion_reasons.append("Victim shows high visual stress.")
        elif visual_stress_level == "MEDIUM":
            fused_score += 8
            fusion_reasons.append("Victim shows moderate visual stress.")
        elif visual_stress_level == "LOW":
            fusion_reasons.append("Victim face visible with low visual stress.")
    else:
        fused_score += 5
        fusion_reasons.append("Victim face not visible during monitoring.")

    # Attention evidence
    if attention_status in ["DISTRACTED", "FACE_NOT_VISIBLE"]:
        fused_score += 5
        fusion_reasons.append("Victim attention is unstable or face is not visible.")

    # Scam pattern evidence
    critical_patterns = [
        "digital arrest",
        "otp",
        "transfer money",
        "verification amount",
        "bank account",
        "money laundering",
        "do not tell anyone",
        "stay on video call",
        "do not disconnect",
    ]

    matched_critical = [
        pattern for pattern in detected_patterns
        if pattern in critical_patterns
    ]

    if len(matched_critical) >= 2:
        fused_score += 10
        fusion_reasons.append("Multiple critical digital arrest scam patterns detected.")

    fused_score = min(100, fused_score)

    if fused_score >= 70:
        fused_level = "HIGH"
        final_action = (
            "High-risk digital arrest fraud detected. Disconnect immediately, "
            "do not share OTP/bank details, and report to 1930."
        )
    elif fused_score >= 35:
        fused_level = "MEDIUM"
        final_action = (
            "Suspicious fraud pattern detected. Verify independently through official channels."
        )
    else:
        fused_level = "LOW"
        final_action = "No major fraud pattern detected yet. Continue monitoring."

    return {
        "fused_risk_score": fused_score,
        "fused_risk_level": fused_level,
        "fusion_reasons": fusion_reasons,
        "final_action": final_action,
        "visual_context": {
            "face_detected": face_detected,
            "visual_stress_level": visual_stress_level,
            "attention_status": attention_status,
        },
    }