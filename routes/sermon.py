from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Request
from utils.transcribe import transcribe_audio
from utils.summarize import generate_summary
from utils.extract_bible import detect_bible_verses
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from models.sermon import Sermon
from schemas.sermon import SermonCreate, SermonOutput, SermonUpdate
from models.user import User
from utils.auth import get_current_user
from config.db import get_session
from datetime import datetime

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

def to_dict(model):
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=True)
    return model.dict(exclude_unset=True)

@router.patch("/{sermon_id}")
async def update_sermon(
            sermon_id: int,
            request: Request,
            session: Session = Depends(get_session),
            current_user: User = Depends(get_current_user),
        ):

            payload = await  request.json()

            sermon = session.exec(select(Sermon).where(
                Sermon.id == sermon_id,
                Sermon.user_id == current_user.id
            )).first()

            if not sermon:
                raise HTTPException(
                    status_code=404,
                    detail="Sermon not found"
                )

            allowed = {"title", "summary", "bible_references"}
            updated = False

            # To update only the provided fields
            for key, value in payload.items():
                if key in allowed:
                    setattr(sermon, key, value)
                    updated = True

            if not updated:
                raise HTTPException(
                    status_code=400,
                    detail="No valid fields to update"
                )

            sermon.updated_at = datetime.utcnow()
            session.add(sermon)
            session.commit()
            session.refresh(sermon)

            return sermon


@router.delete("/{sermon_id}", status_code=204)
def delete_sermon(
            sermon_id: int,
            session: Session = Depends(get_session),
            current_user: User = Depends(get_current_user),
        ):
            sermon = session.query(Sermon).filter(Sermon.id == sermon_id, Sermon.user_id == current_user.id).first()
            if not sermon:
                raise HTTPException(
                    status_code=404,
                    detail="Sermon not found"
                )

            session.delete(sermon)
            session.commit()

            return Response(status_code=204)
