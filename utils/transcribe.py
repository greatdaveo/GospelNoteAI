import os
import tempfile
import ffmpeg
from faster_whisper import WhisperModel

# For LOW-RAM model loader
_MODEL = WhisperModel(
    "tiny",
    device="cpu",
    compute_type="int8",
    download_root="./models"
)

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
        print(" FFMPEG Conversion Error:", error_msg)
        raise RuntimeError(f"FFMPEG failed: {error_msg}")


def transcribe_audio(audio_bytes: bytes, file_extension: str = ".webm") -> str:
    input_path = None
    wav_path = None

    try:
        # Save uploaded bytes with proper extension so FFmpeg can detect format
        ext = file_extension.lower() if file_extension else ".webm"
        if not ext.startswith("."):
            ext = "." + ext
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as input_file:
            input_file.write(audio_bytes)
            input_path = input_file.name

        # Convert to 16k mono WAV & create output .wav path (The smallest RAM footprint for Whisper)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as wav_file:
            wav_path = wav_file.name

        convert_audio(input_path, wav_path)

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
        print(" Transcription failed:", str(e))
        raise

    finally:
        # To clean up
        try:
            if input_path and os.path.exists(input_path):
                os.remove(input_path)
        except Exception:
            pass
        try:
            if wav_path and os.path.exists(wav_path):
                os.remove(wav_path)
        except Exception:
            pass


def transcribe_file(path: str) -> str:
    # Get file extension from path for better format detection
    _, ext = os.path.splitext(path)
    ext = ext if ext else ".webm"  # Default to .webm for browser recordings
    
    with open(path, "rb") as f:
        return transcribe_audio(f.read(), file_extension=ext)