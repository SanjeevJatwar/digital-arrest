from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from .capture import make_audio_chunk, AudioChunk

try:
    import sounddevice as sd
    import numpy as np
except Exception:  # optional dependency
    sd = None
    np = None

try:
    import soundcard as sc
except Exception:
    sc = None

try:
    import cv2
except Exception:
    cv2 = None


def _now_ts() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def get_mic_chunk(index: int, duration: float = 2.0, samplerate: int = 16000) -> AudioChunk:
    if sd is None or np is None:
        return make_audio_chunk(index, 'mic')

    try:
        frames = int(duration * samplerate)
        data = sd.rec(frames, samplerate=samplerate, channels=1, dtype='float32')
        sd.wait()
        rms = float(np.sqrt((data.astype('float64') ** 2).mean()))
        energy = min(0.99, round(rms * 3.5, 2))

        return AudioChunk(
            index=index,
            source='mic',
            speaker=f'SPEAKER_{(index % 2) + 1}',
            transcript_hint='',
            duration_seconds=duration,
            energy=energy,
            timestamp=_now_ts(),
            samples=data.flatten().astype('float32').tolist()
        )
    except Exception:
        return make_audio_chunk(index, 'mic')


def get_system_chunk(index: int, duration: float = 2.0, samplerate: int = 16000) -> AudioChunk:
    # Try to capture loopback / speaker output via soundcard when available.
    if sc is None:
        return make_audio_chunk(index, 'system')

    try:
        speaker = sc.default_speaker()
        with speaker.recorder(samplerate=samplerate) as recorder:
            data = recorder.record(int(duration * samplerate))
        # data may be stereo; compute rms across channels
        arr = data
        if arr is None:
            return make_audio_chunk(index, 'system')
        rms = float(np.sqrt((np.array(arr, dtype='float64') ** 2).mean()))
        energy = min(0.99, round(rms * 3.5, 2))

        return AudioChunk(
            index=index,
            source='system',
            speaker='SYSTEM',
            transcript_hint='',
            duration_seconds=duration,
            energy=energy,
            timestamp=_now_ts(),
            samples=np.array(arr, dtype='float32').reshape(-1).tolist()
        )
    except Exception:
        return make_audio_chunk(index, 'system')


class WebcamCapture:
    def __init__(self) -> None:
        self.cap = None

    def _open(self) -> bool:
        if cv2 is None:
            return False
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
            return True
        except Exception:
            self.cap = None
            return False

    def read_state(self, index: int) -> dict:
        if cv2 is None:
            # fallback synthetic face state
            return {
                'type': 'face_emotion',
                'timestamp': _now_ts(),
                'emotion': 'neutral',
                'gaze': 'center',
                'blink_rate': 0.12
            }

        if self.cap is None and not self._open():
            return {
                'type': 'face_emotion',
                'timestamp': _now_ts(),
                'emotion': 'neutral',
                'gaze': 'center',
                'blink_rate': 0.12
            }

        ret, frame = self.cap.read()
        if not ret or frame is None:
            return {
                'type': 'face_emotion',
                'timestamp': _now_ts(),
                'emotion': 'neutral',
                'gaze': 'center',
                'blink_rate': 0.12
            }

        # Very small placeholder analysis: use brightness to estimate blinkiness
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean = float(gray.mean())
        # Map mean brightness to a fake emotion/gaze/blink rate
        emotion = 'neutral'
        if mean < 40:
            emotion = 'tense'
        elif mean > 160:
            emotion = 'focused'

        gaze = 'center'
        blink_rate = max(0.05, min(0.3, (128.0 - abs(mean - 128.0)) / 512.0))

        return {
            'type': 'face_emotion',
            'timestamp': _now_ts(),
            'emotion': emotion,
            'gaze': gaze,
            'blink_rate': round(blink_rate, 3)
        }


_webcam = WebcamCapture()


def get_face_state(index: int) -> dict:
    return _webcam.read_state(index)
