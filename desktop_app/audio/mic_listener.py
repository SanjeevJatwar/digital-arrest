import sounddevice as sd
import numpy as np
import queue
import wave
import tempfile


class MicListener:
    def __init__(self, samplerate=16000, channels=1, chunk_duration=5):
        self.samplerate = samplerate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.audio_queue = queue.Queue()
        self.is_listening = False
        self.stream = None

    def audio_callback(self, indata, frames, time, status):
        if status:
            print("Audio status:", status)

        if self.is_listening:
            self.audio_queue.put(indata.copy())

    def start(self):
        if self.is_listening:
            return

        self.is_listening = True

        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="int16",
            callback=self.audio_callback,
        )

        self.stream.start()
        print("Microphone listening started.")

    def stop(self):
        self.is_listening = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        print("Microphone listening stopped.")

    def get_audio_chunk(self):
        frames = []
        required_frames = int(self.samplerate * self.chunk_duration)
        collected = 0

        while collected < required_frames and self.is_listening:
            try:
                data = self.audio_queue.get(timeout=1)
                frames.append(data)
                collected += len(data)
            except queue.Empty:
                break

        if frames:
            audio_data = np.concatenate(frames, axis=0)
            return audio_data

        return None

    def save_chunk_to_wav(self, audio_data):
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_path = temp_file.name
        temp_file.close()

        with wave.open(temp_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.samplerate)
            wf.writeframes(audio_data.tobytes())

        return temp_path