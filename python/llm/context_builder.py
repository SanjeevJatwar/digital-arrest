from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass
class ContextSnapshot:
    transcript_lines: list[str]
    stress_score: int
    dominant_face_emotion: str
    voice_emotion: str
    voice_pace: str


class ContextBuilder:
    def __init__(self, context_lines: int = 10) -> None:
        self.context_lines = context_lines

    def build(self, transcript_lines: Iterable[dict], voice_state: dict, face_state: dict) -> ContextSnapshot:
        transcript_text = [
            f"{line.get('speaker', 'SPEAKER')}: {line.get('text', '')}"
            for line in transcript_lines
        ]

        return ContextSnapshot(
            transcript_lines=transcript_text[-self.context_lines:],
            stress_score=int(voice_state.get('stress_score', 0)),
            dominant_face_emotion=face_state.get('emotion', 'neutral'),
            voice_emotion=voice_state.get('emotion', 'neutral'),
            voice_pace=voice_state.get('pace', 'steady')
        )

    def format_prompt(self, context: ContextSnapshot) -> str:
        lines = '\n'.join(context.transcript_lines) or 'No transcript lines yet.'
        return (
            'Analyze the call context and produce a concise two-sentence insight.\n'
            f'Transcript:\n{lines}\n\n'
            f'Voice emotion: {context.voice_emotion}\n'
            f'Voice pace: {context.voice_pace}\n'
            f'Stress score: {context.stress_score}\n'
            f'Dominant face emotion: {context.dominant_face_emotion}'
        )