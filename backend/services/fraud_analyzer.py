def analyze_text(text: str, speaker: str = "unknown") -> dict:
    text_lower = text.lower()

    risk_score = 0
    detected_patterns = []

    scam_keywords = {
        "digital arrest": 40,
        "police": 20,
        "cyber crime": 25,
        "cbi": 20,
        "rbi": 20,
        "customs": 20,
        "warrant": 25,
        "arrest": 25,
        "case filed": 25,
        "money laundering": 30,
        "otp": 35,
        "bank account": 30,
        "transfer money": 40,
        "verification amount": 35,
        "do not tell anyone": 35,
        "stay on video call": 35,
        "do not disconnect": 30,
        "aadhaar": 20,
        "pan card": 20,
    }

    victim_distress_keywords = {
        "i am scared": 20,
        "i am afraid": 20,
        "what should i do": 15,
        "please help": 20,
        "i don't understand": 10,
        "why am i arrested": 15,
    }

    for keyword, score in scam_keywords.items():
        if keyword in text_lower:
            if speaker.lower() in ["caller", "suspicious_caller"]:
                score = int(score * 1.3)
            risk_score += score
            detected_patterns.append(keyword)

    if speaker.lower() in ["victim", "user"]:
        for keyword, score in victim_distress_keywords.items():
            if keyword in text_lower:
                risk_score += score
                detected_patterns.append(f"victim distress: {keyword}")

    risk_score = min(risk_score, 100)

    if risk_score >= 70:
        risk_level = "HIGH"
        recommended_action = (
            "Likely digital arrest scam. Do not share OTP, bank details, "
            "or transfer money. Disconnect immediately."
        )
    elif risk_score >= 35:
        risk_level = "MEDIUM"
        recommended_action = (
            "Suspicious conversation. Verify independently through official channels."
        )
    else:
        risk_level = "LOW"
        recommended_action = (
            "No major scam pattern detected yet. Continue monitoring."
        )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "detected_patterns": detected_patterns,
        "recommended_action": recommended_action,
    }