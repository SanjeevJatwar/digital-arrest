from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


SYSTEM_HINTS = [
    'Zoom audio confirms the host is speaking about the schedule.',
    'The room audio includes a follow-up question and a short pause.',
    'Background call traffic increases slightly before the next reply.',
    'A calm response follows a request for clarification.',
    'The speaker hesitates, then continues with a longer explanation.'
]

MIC_HINTS = [
    'I can send that over in a minute.',
    'I am not sure about that part.',
    'Please let me double check the timeline.',
    'That was not my understanding.',
    'I think the next step is to verify the account details.'
]


@dataclass(frozen=True)
class AudioChunk:
    index: int
    source: str
    speaker: str
    transcript_hint: str
    duration_seconds: float
    energy: float
    timestamp: str


def make_audio_chunk(index: int, source: str) -> AudioChunk:
    source_key = source.lower().strip()
    hints = SYSTEM_HINTS if source_key == 'system' else MIC_HINTS
    transcript_hint = hints[index % len(hints)]
    speaker = 'SYSTEM' if source_key == 'system' else f'SPEAKER_{(index % 2) + 1}'
    energy = 0.32 + ((index % 7) * 0.08)

    return AudioChunk(
        index=index,
        source=source_key,
        speaker=speaker,
        transcript_hint=transcript_hint,
        duration_seconds=2.0,
        energy=min(0.98, round(energy, 2)),
        timestamp=datetime.now(timezone.utc).isoformat(timespec='seconds')
    )