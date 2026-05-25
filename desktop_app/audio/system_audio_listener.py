import soundcard as sc
import numpy as np
import queue
import wave
import tempfile
import threading
import time


class SystemAudioListener:
    def __init__(self, samplerate=48000, channels=2, chunk_duration=5):
        self.samplerate = samplerate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.worker_thread = None
        self.speaker = None

    def start(self):
        if self.is_listening:
            return

        self.is_listening = True

        self.speaker = sc.default_speaker()

        print(f"Selected system speaker loopback: {self.speaker.name}")

        self.worker_thread = threading.Thread(
            target=self._record_loop,
            daemon=True
        )

        self.worker_thread.start()

        print("System audio loopback listening started.")

    def _record_loop(self):
        with sc.get_microphone(
            id=str(self.speaker.name),
            include_loopback=True
        ).recorder(samplerate=self.samplerate) as recorder:

            while self.is_listening:
                audio_data = recorder.record(
                    numframes=int(self.samplerate * self.chunk_duration)
                )

                if audio_data is not None:
                    audio_data = np.array(audio_data)

                    if audio_data.ndim == 1:
                        audio_data = audio_data.reshape(-1, 1)

                    self.audio_queue.put(audio_data)

    def stop(self):
        self.is_listening = False
        time.sleep(0.2)

        print("System audio loopback listening stopped.")

    def get_audio_chunk(self):
        try:
            return self.audio_queue.get(timeout=1)
        except queue.Empty:
            return None

    def save_chunk_to_wav(self, audio_data):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()

        audio_data = np.clip(audio_data, -1.0, 1.0)
        audio_int16 = (audio_data * 32767).astype(np.int16)

        channels = audio_int16.shape[1] if audio_int16.ndim > 1 else 1

        with wave.open(temp_path, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(audio_int16.tobytes())

        return temp_path