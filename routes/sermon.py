from fastapi import APIRouter, UploadFile, File
from utils.transcribe import transcribe_audio
from utils.summarize import generate_summary
from utils.extract_bible import detect_bible_verses
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post("/transcribe")
async def transcribe_sermon(file: UploadFile = File(...)):
    try:
        print("------- 📌 TRANSCRIBE BEGINS: -------")
        audio_bytes = await file.read()
        if not audio_bytes:
            print("No Audio")
            return JSONResponse(
                status_code=400,
                content={"error": "No audio provided"}
            )

        transcript = transcribe_audio(audio_bytes)

        if not transcript:
            print("Empty transcript returned")
            return JSONResponse(
                status_code=500,
                content={"error": "Transcript failed"}
            )

        # print("Transcript length:", len(transcript))
        # print("Transcript Sample:", transcript[:100])

        # To summarize
        summary = generate_summary(transcript)
        # To extract bible verses
        bible_refs = detect_bible_verses(transcript)

        return {
            "transcript": transcript,
            "summary": summary,
            "bible_references": bible_refs
        }

    except Exception as e:
        print("Exception Error:", str(e))
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )
