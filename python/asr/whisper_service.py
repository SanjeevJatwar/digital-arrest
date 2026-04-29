from __future__ import annotations

from typing import Any

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None

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
        if self.backend == 'faster-whisper' and self.model is not None and np is not None:
            # Use captured samples when available; otherwise derive a tiny placeholder waveform.
            samples = getattr(chunk, 'samples', None)
            if samples:
                audio_array = np.array(samples, dtype='float32')
            else:
                sample_count = max(1600, int(chunk.duration_seconds * 16000))
                audio_array = np.full(sample_count, float(chunk.energy) * 0.01, dtype='float32')

            try:
                segments, _ = self.model.transcribe(audio_array, beam_size=5)
                text = ' '.join(seg.text for seg in segments).strip() or chunk.transcript_hint
            except Exception:
                text = chunk.transcript_hint

            return {
                'type': 'transcript_line',
                'timestamp': chunk.timestamp,
                'source': chunk.source,
                'speaker': chunk.speaker,
                'text': text,
                'backend': self.backend
            }

        return {
            'type': 'transcript_line',
            'timestamp': chunk.timestamp,
            'source': chunk.source,
            'speaker': chunk.speaker,
            'text': chunk.transcript_hint,
            'backend': self.backend
        }