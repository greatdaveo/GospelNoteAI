from fastapi import APIRouter, UploadFile, File
from utils.transcribe import transcribe_audio
from utils.summarize import generate_summary
from utils.extract_bible import detect_bible_verses

router = APIRouter()


@router.post("/transcribe")
async def transcribe_sermon(file: UploadFile = File(...)):
    audio_bytes = await file.read()

    # To transcribe
    transcript = transcribe_audio(audio_bytes)
    # To summarize
    summary = generate_summary(transcript)
    # To extract bible verses
    bible_refs = detect_bible_verses(transcript)

    return {
        "transcript": transcript,
        "summary": summary,
        "bible_references": bible_refs
    }
