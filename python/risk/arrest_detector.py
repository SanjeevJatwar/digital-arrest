from __future__ import annotations


class ArrestDetector:
    def __init__(self, threshold: int = 65) -> None:
        self.threshold = threshold

    def evaluate(self, verdict: dict) -> dict:
        arrest_score = int(verdict.get('arrest_score', 0))
        is_alert = arrest_score >= self.threshold
        signal_text = ', '.join(verdict.get('signals', []))

        return {
            'type': 'arrest_alert' if is_alert else 'arrest_monitor',
            'arrest_score': arrest_score,
            'verdict': verdict.get('verdict', 'monitoring'),
            'signals': verdict.get('signals', []),
            'signal_text': signal_text,
            'confidence': verdict.get('confidence', 'low'),
            'alert': is_alert,
            'threshold': self.threshold
        }