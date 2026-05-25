import time
import numpy as np

from desktop_app.audio.system_audio_listener import SystemAudioListener


listener = SystemAudioListener()

print("Starting system audio test...")
print("Play any YouTube video or music now.")

listener.start()

for i in range(10):
    print(f"Recording chunk {i + 1}/5...")
    audio_chunk = listener.get_audio_chunk()

    if audio_chunk is not None:
        volume = np.abs(audio_chunk).mean()
        print(f"System audio volume: {volume:.2f}")
    else:
        print("No system audio captured.")

    time.sleep(1)

listener.stop()

print("System audio test completed.")