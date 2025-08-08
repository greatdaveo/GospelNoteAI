from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from utils.transcribe import transcribe_audio
from utils.summarize import generate_summary
from utils.extract_bible import detect_bible_verses
from fastapi.responses import JSONResponse

from sqlmodel import Session
from models.sermon import Sermon
from schemas.sermon import SermonCreate, SermonOutput
from models.user import User
from utils.auth import get_current_user
from config.db import get_session

router = APIRouter()


@router.post("/transcribe")
async def transcribe_sermon(file: UploadFile = File(...)):
    try:
        print("------- 📌 TRANSCRIBE BEGINS: -------")
        print("Received file:", file.filename)

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
        bible_refs = detect_bible_verses(" ".join(summary))

        print("Bible References: ", bible_refs)

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

@router.post("/save", response_model=SermonOutput)
def save_sermon(
        sermon: SermonCreate,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
    ):
        try:
            new_sermon = Sermon(
                user_id=current_user.id,
                title=sermon.title,
                summary=sermon.summary,
                bible_references=sermon.bible_references,
            )

            session.add(new_sermon)
            session.commit()
            session.refresh(new_sermon)

            return new_sermon
        except Exception as e:
            session.rollback()
            raise  HTTPException(
                    status_code=500,
                    detail="Failed to save sermon"
                )


@router.get("/all-sermons")
def get_sermons(
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
    ):
        sermons = session.query(Sermon).filter(Sermon.user_id == current_user.id).order_by(Sermon.created_at.desc()).all()
        return sermons