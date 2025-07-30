from faster_whisper import WhisperModel

model = WhisperModel("tiny")

segments, info = model.transcribe("5c262b3b-0d98-40ca-9cb1-d3bade333ab6.mp3")

print("Detected language:", info.language)
for segment in segments:
    print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
