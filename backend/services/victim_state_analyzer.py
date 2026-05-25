def analyze_victim_state(
    victim_text: str,
    visual_stress_level: str = "UNKNOWN",
    attention_status: str = "UNKNOWN",
    face_detected: bool = False,
) -> dict:

    text = victim_text.lower()

    internal_support_score = 0
    observed_signals = []
    supportive_interventions = []

    fear_phrases = [
        "i am scared",
        "i am afraid",
        "i am worried",
        "i am nervous",
        "please help",
        "i don't know what to do",
    ]

    denial_phrases = [
        "i have not done anything",
        "i didn't do anything",
        "i am innocent",
        "i am not involved",
        "this is not mine",
        "i don't know anything",
        "i have not done anything sir",
    ]

    confusion_phrases = [
        "what should i do",
        "what happened",
        "i don't understand",
        "why am i arrested",
        "why are you saying this",
        "what is my mistake",
    ]

    compliance_pressure_phrases = [
        "okay sir",
        "yes sir",
        "i will do it",
        "i am doing it",
        "please don't",
        "don't arrest me",
    ]

    for phrase in fear_phrases:
        if phrase in text:
            internal_support_score += 25
            observed_signals.append("Victim language suggests fear or worry.")

    for phrase in denial_phrases:
        if phrase in text:
            internal_support_score += 20
            observed_signals.append("Victim is repeatedly denying wrongdoing.")

    for phrase in confusion_phrases:
        if phrase in text:
            internal_support_score += 15
            observed_signals.append("Victim appears confused about the situation.")

    for phrase in compliance_pressure_phrases:
        if phrase in text:
            internal_support_score += 15
            observed_signals.append("Victim may be responding under pressure.")

    if visual_stress_level == "HIGH":
        internal_support_score += 20
        observed_signals.append("Visual monitoring indicates possible distress.")

    elif visual_stress_level == "MEDIUM":
        internal_support_score += 10
        observed_signals.append("Visual monitoring indicates mild concern.")

    if attention_status in ["DISTRACTED", "FACE_NOT_VISIBLE"]:
        internal_support_score += 8
        observed_signals.append("Victim attention appears unstable or face is not clearly visible.")

    if not face_detected:
        internal_support_score += 5
        observed_signals.append("Victim face is not consistently visible.")

    internal_support_score = min(internal_support_score, 100)

    if internal_support_score >= 70:
        support_status = "Immediate Support Recommended"
        support_summary = (
            "The victim may be under significant pressure. "
            "Provide calm reassurance and advise immediate call disconnection."
        )
        supportive_interventions = [
            "Reassure the victim that they are safe.",
            "Tell them not to share OTP, bank details, or money.",
            "Advise them to disconnect the call immediately.",
            "Encourage them to contact a trusted person or cybercrime helpline 1930.",
        ]

    elif internal_support_score >= 40:
        support_status = "Support Recommended"
        support_summary = (
            "The victim shows possible signs of confusion or pressure. "
            "Guide them to pause and verify independently."
        )
        supportive_interventions = [
            "Pause before responding.",
            "Do not share sensitive information.",
            "You are safe. This appears suspicious. Disconnect if you feel pressured.",
        ]

    elif internal_support_score >= 15:
        support_status = "Monitor Closely"
        support_summary = (
            "Some concern signals are present. Continue monitoring and provide gentle guidance."
        )
        supportive_interventions = [
            "Continue monitoring the interaction.",
            "Pause before taking any action. Do not respond under pressure.",
        ]

    else:
        support_status = "No Immediate Support Signal"
        support_summary = (
            "No strong victim distress signal detected yet. Continue monitoring respectfully."
        )
        supportive_interventions = [
            "Continue passive monitoring.",
        ]

    if not observed_signals:
        observed_signals.append("No strong victim distress signal detected yet.")

    return {
        "support_status": support_status,
        "support_summary": support_summary,
        "observed_signals": list(set(observed_signals)),
        "supportive_interventions": supportive_interventions,

        # Internal only. Do not display directly in UI.
        "internal_support_score": internal_support_score,
    }