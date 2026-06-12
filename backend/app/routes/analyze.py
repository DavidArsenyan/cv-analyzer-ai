from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas import AnalysisHistoryItem, ResumeAnalysisResponse
from app.services.analysis import analyze_resume
from app.services.auth import get_current_user, get_optional_user
from app.services.history import list_user_analysis_records, save_analysis_record
from app.services.resume_parser import extract_resume_text, validate_resume_text_content
from app.services.security import rate_limit_analysis, validate_resume_upload


router = APIRouter(tags=["analysis"])


@router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_cv(
    request: Request,
    resume: UploadFile = File(...),
    job_description: Optional[str] = Form(default=None),
    analysis_mode: str = Form(default="openai"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> ResumeAnalysisResponse:
    rate_limit_analysis(request, user_id=current_user.id if current_user else None)

    if not resume.filename:
        raise HTTPException(status_code=400, detail="Resume file is required.")

    file_bytes = await resume.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    validate_resume_upload(resume.filename, file_bytes)

    try:
        resume_text = extract_resume_text(resume.filename, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        validate_resume_text_content(resume_text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    result = analyze_resume(
        resume_text=resume_text,
        job_description=job_description,
        analysis_mode=analysis_mode,
    )
    if current_user:
        save_analysis_record(
            db=db,
            user_id=current_user.id,
            filename=resume.filename,
            result=result,
            target_role=_target_role_from_job_description(job_description),
        )
    return result


@router.get("/analyses", response_model=list[AnalysisHistoryItem])
def get_analysis_history(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnalysisHistoryItem]:
    return list_user_analysis_records(db=db, user_id=current_user.id, limit=min(max(limit, 1), 50))


def _target_role_from_job_description(job_description: Optional[str]) -> Optional[str]:
    if not job_description:
        return None

    cleaned = " ".join(job_description.strip().split())
    if not cleaned:
        return None

    first_line = cleaned.split(".")[0].strip()
    title = first_line if len(first_line) <= 80 else cleaned[:80].rstrip()
    return title or None
