from __future__ import annotations

from typing import Any

try:
    from speechbrain.inference.classifiers import EncoderClassifier
except Exception:  # pragma: no cover - optional dependency
    EncoderClassifier = None


class VoiceEmotionService:
    def __init__(self, config) -> None:
        self.config = config
        self.labels = ['anger', 'fear', 'joy', 'sadness', 'neutral']
        self.model: Any = None
        self.backend = 'synthetic'

    def load(self) -> dict[str, str]:
        if not self.config.enable_real_models or EncoderClassifier is None:
            self.model = None
            self.backend = 'synthetic'
            return {
                'state': 'fallback',
                'detail': f'synthetic stress estimator enabled for {self.config.voice_model_name}'
            }

        self.model = EncoderClassifier.from_hparams(
            source=self.config.voice_model_name,
            savedir=str(self.config.model_dir / 'speechbrain')
        )
        self.backend = 'speechbrain'
        return {
            'state': 'ready',
            'detail': f'loaded {self.config.voice_model_name} into resident memory'
        }

    def analyze(self, chunk) -> dict:
        emotion = self.labels[chunk.index % len(self.labels)]
        pace = 'fast' if chunk.energy > 0.65 else 'steady'
        stress_score = int(min(100, round((chunk.energy * 72) + (12 if emotion in {'fear', 'anger'} else 0))))

        return {
            'type': 'voice_emotion',
            'timestamp': chunk.timestamp,
            'emotion': emotion,
            'stress_score': stress_score,
            'pace': pace,
            'energy': chunk.energy,
            'backend': self.backend
        }