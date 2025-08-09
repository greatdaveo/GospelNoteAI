import os
import tempfile
import ffmpeg
from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="float32")

def convert_audio(input_path: str, output_path: str):
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, acodec="pcm_s16le", ac=1, ar="16k")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else "Unknown ffmpeg error"
        print("❌ FFMPEG Conversion Error:", error_msg)
        raise RuntimeError(f"FFMPEG failed: {error_msg}")

def transcribe_audio(audio_bytes: bytes) -> str:
    # To save uploaded bytes as .m4a
    with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as m4a_file:
        m4a_file.write(audio_bytes)
        m4a_path = m4a_file.name

    # To create output .wav path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
        wav_path = wav_file.name

    # To try conversion
    try:
        convert_audio(m4a_path, wav_path)
    except Exception as e:
        print("❌ Conversion failed:", str(e))
        os.remove(m4a_path)
        raise

    # To transcribe with Whisper
    try:
        segments, info = model.transcribe(wav_path)
    except Exception as e:
        print("❌ Transcription failed:", str(e))
        raise

    full_text = ""
    for segment in segments:
        print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
        full_text += segment.text.strip() + " "

    # To clean up
    os.remove(m4a_path)
    os.remove(wav_path)

    return full_text.strip()
