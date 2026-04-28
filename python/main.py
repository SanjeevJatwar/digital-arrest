from __future__ import annotations

import asyncio
import json
import threading
import time
from collections import deque
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn

from config import BackendConfig
from audio.capture import make_audio_chunk
from audio.capture_adapters import get_mic_chunk, get_system_chunk, get_face_state
from services.model_registry import ModelRegistry
from llm.context_builder import ContextBuilder
from risk.arrest_detector import ArrestDetector


CONFIG = BackendConfig()


class ProcessOrchestrator:
    def __init__(self, config: BackendConfig, registry: ModelRegistry) -> None:
        self.config = config
        self.registry = registry
        self.loop: asyncio.AbstractEventLoop | None = None
        self.audio_queue: asyncio.Queue[Any] = asyncio.Queue()
        self.voice_queue: asyncio.Queue[Any] = asyncio.Queue()
        self.outbound_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self.transcript_buffer: deque[dict[str, Any]] = deque(maxlen=30)
        self.voice_state: dict[str, Any] = {
            'emotion': 'neutral',
            'stress_score': 18,
            'pace': 'steady',
            'energy': 0.35
        }
        self.face_state: dict[str, Any] = {
            'emotion': 'neutral',
            'gaze': 'center',
            'blink_rate': 0.12
        }
        self.running = False
        self.threads: list[threading.Thread] = []
        self.whisper = registry.whisper
        self.voice_emotion = registry.voice
        self.context_builder = ContextBuilder(config.llm_context_lines)
        self.phi = registry.llm
        self.detector = ArrestDetector(config.arrest_threshold)

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop
        self.running = True
        self.threads = [
            threading.Thread(target=self._audio_worker, daemon=True),
            threading.Thread(target=self._stt_worker, daemon=True),
            threading.Thread(target=self._voice_worker, daemon=True),
            threading.Thread(target=self._face_worker, daemon=True),
            threading.Thread(target=self._context_worker, daemon=True)
        ]

        for thread in self.threads:
            thread.start()

    def stop(self) -> None:
        self.running = False

    def _emit(self, payload: dict[str, Any]) -> None:
        if self.loop is None:
            return

        self.loop.call_soon_threadsafe(self.outbound_queue.put_nowait, payload)

    def _push_queue(self, queue: asyncio.Queue[Any], item: Any) -> None:
        if self.loop is None:
            return

        self.loop.call_soon_threadsafe(queue.put_nowait, item)

    def _pull_queue(self, queue: asyncio.Queue[Any]) -> Any:
        if self.loop is None:
            return None

        future = asyncio.run_coroutine_threadsafe(queue.get(), self.loop)
        return future.result()

    def _audio_worker(self) -> None:
        index = 0
        while self.running:
            if self.config.enable_real_capture:
                system_chunk = get_system_chunk(index)
                mic_chunk = get_mic_chunk(index)
            else:
                system_chunk = make_audio_chunk(index, 'system')
                mic_chunk = make_audio_chunk(index, 'mic')

            self._push_queue(self.audio_queue, system_chunk)
            self._push_queue(self.voice_queue, mic_chunk)

            index += 1
            time.sleep(self.config.frame_rate if hasattr(self.config, 'frame_rate') else 2.0)

    def _stt_worker(self) -> None:
        while self.running:
            chunk = self._pull_queue(self.audio_queue)
            if chunk is None:
                continue

            transcript = self.whisper.transcribe(chunk)
            self.transcript_buffer.append(transcript)
            self._emit(transcript)

    def _voice_worker(self) -> None:
        while self.running:
            chunk = self._pull_queue(self.voice_queue)
            if chunk is None:
                continue

            voice_state = self.voice_emotion.analyze(chunk)
            self.voice_state = voice_state
            self._emit(voice_state)

    def _face_worker(self) -> None:
        index = 0
        while self.running:
            if self.config.enable_real_capture:
                face_state = get_face_state(index)
            else:
                emotion_cycle = ['neutral', 'concerned', 'tense', 'neutral', 'focused']
                gaze_cycle = ['center', 'left', 'right', 'center', 'down']
                blink_cycle = [0.10, 0.12, 0.18, 0.14, 0.09]

                face_state = {
                    'type': 'face_emotion',
                    'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                    'emotion': emotion_cycle[index % len(emotion_cycle)],
                    'gaze': gaze_cycle[index % len(gaze_cycle)],
                    'blink_rate': blink_cycle[index % len(blink_cycle)]
                }

            self.face_state = face_state
            self._emit(face_state)
            index += 1
            time.sleep(0.2)

    def _context_worker(self) -> None:
        while self.running:
            time.sleep(8.0)

            context = self.context_builder.build(
                list(self.transcript_buffer),
                self.voice_state,
                self.face_state
            )

            self._emit({'type': 'llm_start'})

            result = self.phi.generate(context)
            for token in result['tokens']:
                self._emit({'type': 'llm_token', 'token': token})
                time.sleep(0.06)

            self._emit({'type': 'llm_insight', 'insight': result['insight']})

            verdict = self.detector.evaluate(result['verdict'])
            if verdict['alert']:
                self._emit(verdict)


app = FastAPI(title='Digital Arrest Backend', version='0.1.0')
model_registry = ModelRegistry(CONFIG)
orchestrator = ProcessOrchestrator(CONFIG, model_registry)


@app.on_event('startup')
async def on_startup() -> None:
    model_status = model_registry.bootstrap()
    for status in model_status:
        print(f"MODEL_{status['name'].upper()}_{status['state'].upper()}: {status['detail']}", flush=True)
    orchestrator.start(asyncio.get_running_loop())
    print('BACKEND_READY', flush=True)


@app.on_event('shutdown')
async def on_shutdown() -> None:
    orchestrator.stop()


@app.get('/health')
async def health() -> dict[str, str]:
    return {'status': 'ok'}


@app.get('/state')
async def state() -> dict[str, Any]:
    return {
        'config': {
            'enable_real_models': CONFIG.enable_real_models,
            'enable_real_capture': CONFIG.enable_real_capture,
            'frame_rate': CONFIG.frame_rate,
            'threshold': CONFIG.arrest_threshold
        },
        'models': [status.__dict__ for status in model_registry.status],
        'transcript_lines': len(orchestrator.transcript_buffer)
    }


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        while True:
            event = await orchestrator.outbound_queue.get()
            await websocket.send_text(json.dumps(event))
    except WebSocketDisconnect:
        return


def main() -> None:
    uvicorn.run(app, host=CONFIG.host, port=CONFIG.port, log_level='warning')


if __name__ == '__main__':
    main()