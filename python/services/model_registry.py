from __future__ import annotations

from dataclasses import dataclass

from config import BackendConfig
from asr.whisper_service import WhisperService
from audio.voice_emotion import VoiceEmotionService
from llm.phi_service import PhiInsightService


@dataclass
class ModelStatus:
    name: str
    state: str
    detail: str


class ModelRegistry:
    def __init__(self, config: BackendConfig) -> None:
        self.config = config
        self.whisper = WhisperService(config)
        self.voice = VoiceEmotionService(config)
        self.llm = PhiInsightService(config)
        self.status: list[ModelStatus] = []

    def bootstrap(self) -> list[dict[str, str]]:
        self.status = [
            self._wrap('whisper', self.whisper.load()),
            self._wrap('voice', self.voice.load()),
            self._wrap('llm', self.llm.load()),
        ]
        return [status.__dict__ for status in self.status]

    def _wrap(self, name: str, result: dict[str, str]) -> ModelStatus:
        return ModelStatus(
            name=name,
            state=result.get('state', 'ready'),
            detail=result.get('detail', 'loaded')
        )
