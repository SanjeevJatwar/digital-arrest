from faster_whisper import WhisperModel

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)


def transcribe_audio(audio_path: str) -> str:
    segments, info = model.transcribe(
        audio_path,
        beam_size=5,
        language="en"
    )

    text_parts = []

    for segment in segments:
        text_parts.append(segment.text.strip())

    return " ".join(text_parts).strip()