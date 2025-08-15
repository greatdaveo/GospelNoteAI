import os
import tempfile
import ffmpeg
from faster_whisper import WhisperModel

# For LOW-RAM model loader
_MODEL = None

# model = WhisperModel("base", device="cpu", compute_type="float32")


def get_model() -> WhisperModel:
    global _MODEL
    if _MODEL is None:
        _MODEL = WhisperModel(
            "tiny",  # For 512MB dyno
            device="cpu",
            compute_type="int8"  # For massive RAM savings
        )
    return _MODEL


# For the FFmpeg Audio conversion
def convert_audio(input_path: str, output_path: str):
    try:
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                acodec="pcm_s16le",  # 16-bit PCM
                ac=1,  # mono
                ar="16000",  # 16 kHz
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )

    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else "Unknown ffmpeg error"
        print("❌ FFMPEG Conversion Error:", error_msg)
        raise RuntimeError(f"FFMPEG failed: {error_msg}")


def transcribe_audio(audio_bytes: bytes) -> str:
    m4a_path = None
    wav_path = None

    try:
        # To save uploaded bytes as .m4a
        with tempfile.NamedTemporaryFile(delete=False, suffix=".m4a") as m4a_file:
            m4a_file.write(audio_bytes)
            m4a_path = m4a_file.name

        # To convert to 16k mono WAV & create output .wav path (The smallest RAM footprint for Whisper)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
            wav_path = wav_file.name

        convert_audio(m4a_path, wav_path)

        # To get the shared model (loaded once)
        model = get_model()
        # To transcribe with Whisper memory friendly settings
        segments, info = model.transcribe(
            wav_path,
            beam_size=1,  # To disable beam search less RAM
            best_of=1,
            vad_filter=False,  # For lower RAM/CPU
            chunk_length=15,  # To process in small chunks
            temperature=0.0
        )

        parts = []
        for segment in segments:
            print(f"[{segment.start:.2f}s - {segment.end:.2f}s] {segment.text}")
            parts.append(segment.text.strip())

        return " ".join(parts).strip()

    except Exception as e:
        print("❌ Transcription failed:", str(e))
        raise

    finally:
        # To clean up
        try:
            if m4a_path and os.path.exists(m4a_path):
                os.remove(m4a_path)
        except Exception:
            pass
        try:
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass


def transcribe_file(path: str) -> str:
    with open(path, "rb") as f:
        return transcribe_audio(f.read())