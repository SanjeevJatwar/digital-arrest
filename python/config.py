from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


@dataclass(frozen=True)
class BackendConfig:
    host: str = os.getenv('DIGITAL_ARREST_HOST', '127.0.0.1')
    port: int = int(os.getenv('DIGITAL_ARREST_PORT', '8765'))
    model_dir: Path = Path(__file__).resolve().parent.parent / 'models'
    enable_real_models: bool = _env_flag('DIGITAL_ARREST_ENABLE_REAL_MODELS', True)
    enable_real_capture: bool = _env_flag('DIGITAL_ARREST_ENABLE_REAL_CAPTURE', False)
    whisper_model_name: str = os.getenv('DIGITAL_ARREST_WHISPER_MODEL', 'large-v3-turbo')
    voice_model_name: str = os.getenv(
        'DIGITAL_ARREST_VOICE_MODEL',
        'speechbrain/emotion-recognition-wav2vec2-IEMOCAP'
    )
    llm_model_path: str = os.getenv('DIGITAL_ARREST_LLM_MODEL_PATH', '')
    llm_context_lines: int = int(os.getenv('DIGITAL_ARREST_CONTEXT_LINES', '10'))
    llm_temperature: float = float(os.getenv('DIGITAL_ARREST_LLM_TEMPERATURE', '0.3'))
    arrest_threshold: int = int(os.getenv('DIGITAL_ARREST_ARREST_THRESHOLD', '65'))
    frame_rate: int = int(os.getenv('DIGITAL_ARREST_FRAME_RATE', '2'))
