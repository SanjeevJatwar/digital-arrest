def generate_live_guidance(
    fused_risk_level: str,
    fused_risk_score: int,
    scam_type: str,
    detected_patterns: list,
    context_text: str,
) -> dict:

    context_lower = context_text.lower()

    guidance = []
    escalation_level = "NORMAL"

    if fused_risk_level == "HIGH":
        escalation_level = "CRITICAL"
        guidance.append("Disconnect the call immediately.")
        guidance.append("Do not share OTP, Aadhaar, PAN, bank details, or screen access.")
        guidance.append("Do not transfer money for verification, clearance, or investigation.")
        guidance.append("Contact 1930 cybercrime helpline or report through the official cybercrime portal.")

    elif fused_risk_level == "MEDIUM":
        escalation_level = "WARNING"
        guidance.append("Pause before responding to the caller.")
        guidance.append("Ask for official written notice through verified government channels.")
        guidance.append("Do not share sensitive information until independently verified.")

    else:
        escalation_level = "MONITORING"
        guidance.append("Continue monitoring. No critical scam pattern detected yet.")

    if "digital arrest" in detected_patterns:
        guidance.append("Remember: there is no legal process called digital arrest.")

    if "do not tell anyone" in detected_patterns:
        guidance.append("The caller is trying to isolate you. Inform a trusted person immediately.")

    if "stay on video call" in detected_patterns or "do not disconnect" in detected_patterns:
        guidance.append("A genuine authority will not force you to stay continuously on video call.")

    if "otp" in detected_patterns:
        guidance.append("Never share OTP with anyone, including people claiming to be police or bank officials.")

    if "transfer money" in detected_patterns or "verification amount" in detected_patterns:
        guidance.append("No genuine law enforcement agency asks for money transfer to verify innocence.")

    if "money laundering" in detected_patterns:
        guidance.append("Money laundering accusations are commonly used in digital arrest scams to create panic.")

    if "screen share" in context_lower or "anydesk" in context_lower or "remote access" in context_lower:
        guidance.append("Do not allow screen sharing or remote access apps like AnyDesk or TeamViewer.")

    primary_message = guidance[0] if guidance else "Continue monitoring."

    return {
        "escalation_level": escalation_level,
        "primary_message": primary_message,
        "guidance_steps": guidance,
    }