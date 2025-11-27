import tempfile
import os
import uuid
import traceback
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, Response
from starlette import status
from typing import Dict, Any
from sqlmodel import Session, select
from models.sermon import Sermon
from schemas.sermon import SermonCreate, SermonOutput, SermonUpdate
from models.user import User
from utils.auth import get_current_user
from utils.transcribe import transcribe_audio, transcribe_file
from utils.summarize import generate_summary
from utils.extract_bible import detect_bible_verses
from config.db import get_session
from datetime import datetime

router = APIRouter()

# To set native in-memory job store (for a single render instance)
JOBS: Dict[str, Dict[str, Any]] = {}


def _process_job(job_id: str, tmp_path: str):
    try:
        JOBS[job_id]["status"] = "processing"
        # To transcribe
        transcript = transcribe_file(tmp_path)
        # To summarize and extract bible verses
        summary = generate_summary(transcript)
        joined = " ".join(summary)[:4000]  # To prevent sending huge text
        bible_refs = detect_bible_verses(joined)
        # If successful
        JOBS[job_id].update({
            "status": "done",
            "result": {
                "transcript": transcript,
                "summary": summary,
                "bible_references": bible_refs,
            },
            "error": None
        })

    except Exception as e:
        # To record the error instead of throwing a 500
        JOBS[job_id].update({
            "status": "error",
            "error": str(e),
            "trace": traceback.format_exc(),
            "result": None,
        })
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


@router.post("/transcribe", status_code=202)
async def start_transcription(background: BackgroundTasks, file: UploadFile = File(...)):
    # To save upload to a temp file & avoid to load all file into RAM
    suffix = os.path.splitext(file.filename or ".m4a")[-1] or ".m4a"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp_path = tmp.name
        while chunk := await file.read(1024 * 1024):
            tmp.write(chunk)

    job_id = uuid.uuid4().hex
    JOBS[job_id] = {"status": "queued", "result": None, "error": None}

    background.add_task(_process_job, job_id, tmp_path)

    # For client to poll GET /api/sermon/transcribe/{job_id}
    return {
        "job_id": job_id,
        "status": "queued",
    }

@router.get("/transcribe/{job_id}")
def get_transcription(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    if job["status"] == "done":
        return {"status": "done", **job["result"]}

    if job["status"] == "error":
        return JSONResponse(
            status_code=500,
            content={"status": "error", "error": job["error"]},
        )

    # To start queue or processing
    return {"status": job["status"]}


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
        raise HTTPException(
            status_code=500,
            detail="Failed to save sermon"
        )


@router.get("/all-sermons")
def get_sermons(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    sermons = (
        session.query(Sermon)
       .filter(Sermon.user_id == current_user.id)
       .order_by(Sermon.created_at.desc())
       .all()
    )
    return sermons


@router.patch("/{sermon_id}")
async def update_sermon(
    sermon_id: int,
    request: Request,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):

    payload = await request.json()

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
    sermon = session.query(Sermon).filter(
        Sermon.id == sermon_id, Sermon.user_id == current_user.id).first()
    if not sermon:
        raise HTTPException(
            status_code=404,
            detail="Sermon not found"
        )

    session.delete(sermon)
    session.commit()

    return Response(status_code=204)
