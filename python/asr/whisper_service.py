from __future__ import annotations

from typing import Any

try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover - optional dependency
    WhisperModel = None


class WhisperService:
    def __init__(self, config) -> None:
        self.config = config
        self.model_name = config.whisper_model_name
        self.model: Any = None
        self.backend = 'synthetic'

    def load(self) -> dict[str, str]:
        if not self.config.enable_real_models or WhisperModel is None:
            self.model = None
            self.backend = 'synthetic'
            return {
                'state': 'fallback',
                'detail': f'synthetic transcript hints enabled for {self.model_name}'
            }

        self.model = WhisperModel(
            self.model_name,
            device='cuda',
            compute_type='float16',
            download_root=str(self.config.model_dir)
        )
        self.backend = 'faster-whisper'
        return {
            'state': 'ready',
            'detail': f'loaded {self.model_name} into resident memory'
        }

    def transcribe(self, chunk) -> dict:
        return {
            'type': 'transcript_line',
            'timestamp': chunk.timestamp,
            'source': chunk.source,
            'speaker': chunk.speaker,
            'text': chunk.transcript_hint,
            'backend': self.backend
        }