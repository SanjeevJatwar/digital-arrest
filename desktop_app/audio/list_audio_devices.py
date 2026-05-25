import sounddevice as sd

print("\nHost APIs:")
for i, api in enumerate(sd.query_hostapis()):
    print(f"{i}: {api['name']}")

print("\nAudio Devices:")
devices = sd.query_devices()

for i, device in enumerate(devices):
    print(
        f"{i}: {device['name']} | "
        f"Input: {device['max_input_channels']} | "
        f"Output: {device['max_output_channels']} | "
        f"HostAPI: {device['hostapi']} | "
        f"Default SR: {device['default_samplerate']}"
    )

print("\nDefault devices:")
print(sd.default.device)