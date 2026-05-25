def generate_scam_reasoning(
    context_text: str,
    detected_patterns: list,
    fused_risk_score: int,
    fused_risk_level: str,
    visual_context: dict | None = None,
) -> dict:

    context_lower = context_text.lower()
    visual_context = visual_context or {}

    scam_type = "Unknown"
    confidence = "Low"
    reasons = []
    safety_steps = []

    if any(pattern in detected_patterns for pattern in [
        "digital arrest",
        "arrest",
        "warrant",
        "money laundering",
        "cyber crime",
        "police",
        "cbi",
        "customs",
    ]):
        scam_type = "Digital Arrest / Fake Law Enforcement Scam"

    if "money laundering" in detected_patterns:
        reasons.append("Caller mentioned money laundering to create fear.")

    if "arrest" in detected_patterns or "warrant" in detected_patterns:
        reasons.append("Caller used arrest or warrant threats.")

    if "digital arrest" in detected_patterns:
        reasons.append("Caller used the phrase digital arrest, which is a known scam pattern.")

    if "bank account" in detected_patterns:
        reasons.append("Caller asked about bank account details.")

    if "otp" in detected_patterns:
        reasons.append("Caller requested or pressured for OTP sharing.")

    if "transfer money" in detected_patterns or "verification amount" in detected_patterns:
        reasons.append("Caller attempted to create a payment or verification money demand.")

    if "do not tell anyone" in detected_patterns:
        reasons.append("Caller tried to isolate the victim from family or authorities.")

    if "stay on video call" in detected_patterns or "do not disconnect" in detected_patterns:
        reasons.append("Caller tried to keep the victim continuously controlled on call.")

    if "court order" in context_lower:
        reasons.append("Caller referred to a court order to increase pressure.")

    if "camera" in context_lower and "turn off" in context_lower:
        reasons.append("Caller pressured the victim to keep camera/video active.")

    if visual_context.get("face_detected") is False:
        reasons.append("Victim face was not consistently visible during monitoring.")

    if visual_context.get("visual_stress_level") in ["MEDIUM", "HIGH"]:
        reasons.append(
            f"Victim showed {visual_context.get('visual_stress_level').lower()} visual stress."
        )

    if fused_risk_score >= 80:
        confidence = "Very High"
    elif fused_risk_score >= 70:
        confidence = "High"
    elif fused_risk_score >= 35:
        confidence = "Medium"
    else:
        confidence = "Low"

    if not reasons:
        reasons.append("No strong scam reasoning pattern found yet.")

    if fused_risk_level == "HIGH":
        safety_steps = [
            "Disconnect the call immediately.",
            "Do not share OTP, Aadhaar, PAN, bank details, or screen access.",
            "Do not transfer money for verification or clearance.",
            "Call 1930 or report on the official cybercrime portal.",
            "Inform a trusted family member or local police station independently.",
        ]
    elif fused_risk_level == "MEDIUM":
        safety_steps = [
            "Pause the conversation and verify independently.",
            "Do not share financial or identity information.",
            "Ask for official written notice through verified channels.",
        ]
    else:
        safety_steps = [
            "Continue monitoring the conversation.",
            "Stay cautious if authority, money, or secrecy pressure appears.",
        ]

    return {
        "scam_type": scam_type,
        "confidence": confidence,
        "reasoning_summary": " ".join(reasons),
        "reasons": reasons,
        "safety_steps": safety_steps,
    }