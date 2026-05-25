class ConversationMemory:
    def __init__(self):
        self.turns = []
        self.max_turns = 30
        self.highest_risk_score = 0
        self.highest_risk_level = "LOW"
        self.detected_patterns = set()

    def add_turn(self, speaker: str, text: str):
        if text and text.strip():
            self.turns.append({
                "speaker": speaker,
                "text": text.strip()
            })

        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns:]

    def get_context_text(self) -> str:
        return " ".join([
            f"{turn['speaker']}: {turn['text']}"
            for turn in self.turns
        ])

    def update_risk(self, analysis: dict):
        score = analysis.get("risk_score", 0)
        patterns = analysis.get("detected_patterns", [])

        self.highest_risk_score = max(self.highest_risk_score, score)

        if self.highest_risk_score >= 70:
            self.highest_risk_level = "HIGH"
        elif self.highest_risk_score >= 35:
            self.highest_risk_level = "MEDIUM"
        else:
            self.highest_risk_level = "LOW"

        for pattern in patterns:
            self.detected_patterns.add(pattern)

    def get_state(self):
        return {
            "context_text": self.get_context_text(),
            "cumulative_risk_score": self.highest_risk_score,
            "cumulative_risk_level": self.highest_risk_level,
            "all_detected_patterns": list(self.detected_patterns),
            "turns": self.turns
        }

    def reset(self):
        self.turns = []
        self.highest_risk_score = 0
        self.highest_risk_level = "LOW"
        self.detected_patterns = set()