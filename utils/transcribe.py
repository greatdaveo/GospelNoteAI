from faster_whisper import WhisperModel
import tempfile
import os

# To load the model once the application starts
model = WhisperModel("base")

def transcribe_audio(audio_bytes: bytes) -> str:
    # To write the audio to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")as temp_file:
        temp_file.write(audio_bytes)
        temp_file_path = temp_file.name

    # To transcribe the file
    segments, info = model.transcribe(temp_file_path)

    # print("Detected language:", info.language)

    full_text = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
        full_text += segment.text.strip() + " "
        # print(full_text.strip())

    # To clean up the file
    os.remove(temp_file_path)

    return full_text.strip()