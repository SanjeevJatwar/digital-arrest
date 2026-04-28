from __future__ import annotations

from typing import Any

try:
    from llama_cpp import Llama
except Exception:  # pragma: no cover - optional dependency
    Llama = None


class PhiInsightService:
    def __init__(self, config) -> None:
        self.config = config
        self.model_name = config.llm_model_path or 'Phi-3-mini-4k-instruct-q4.gguf'
        self.model: Any = None
        self.backend = 'synthetic'

    def load(self) -> dict[str, str]:
        if not self.config.enable_real_models or Llama is None or not self.config.llm_model_path:
            self.model = None
            self.backend = 'synthetic'
            return {
                'state': 'fallback',
                'detail': 'synthetic insight generator enabled until a GGUF path is configured'
            }

        self.model = Llama(
            model_path=self.config.llm_model_path,
            n_ctx=4096,
            n_gpu_layers=-1,
            verbose=False
        )
        self.backend = 'llama-cpp'
        return {
            'state': 'ready',
            'detail': f'loaded {self.config.llm_model_path} into resident memory'
        }

    def generate(self, context) -> dict:
        transcript_count = len(context.transcript_lines)
        voice_line = context.voice_emotion
        face_line = context.dominant_face_emotion
        stress_score = context.stress_score

        if stress_score >= 75 or voice_line in {'fear', 'anger'}:
            signals = ['voice tension', 'hesitation', 'facial strain']
            verdict = 'high stress detected'
            arrest_score = min(100, stress_score + 12)
        elif stress_score >= 45:
            signals = ['moderate stress', 'call friction']
            verdict = 'elevated stress detected'
            arrest_score = min(100, stress_score + 4)
        else:
            signals = ['stable tone', 'low volatility']
            verdict = 'stable call state'
            arrest_score = max(0, stress_score - 10)

        insight = (
            f'The caller is showing {voice_line} cues while the face remains {face_line}. '
            f'Across {transcript_count} recent lines, the call reads as {verdict.lower()}.'
        )

        tokens = insight.split()

        return {
            'type': 'llm_result',
            'insight': insight,
            'tokens': tokens,
            'backend': self.backend,
            'verdict': {
                'arrest_score': arrest_score,
                'verdict': verdict,
                'signals': signals,
                'confidence': 'medium' if arrest_score >= 50 else 'low'
            }
        }