from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.models.user import User
from app.schemas import CoverLetterResponse, InterviewQuestionsResponse, RewriteSectionResponse
from app.services.auth import get_current_user
from app.services.content_generator import generate_cover_letter, generate_interview_questions, rewrite_resume_section
from app.services.resume_parser import extract_resume_text, validate_resume_text_content
from app.services.security import rate_limit_generation, validate_resume_upload


router = APIRouter(tags=["generation"])
ALLOWED_REWRITE_SECTIONS = {"summary", "experience", "skills"}


@router.post(
    "/generate/cover-letter",
    response_model=CoverLetterResponse,
    dependencies=[Depends(rate_limit_generation)],
)
async def create_cover_letter(
    resume: UploadFile = File(...),
    job_description: Optional[str] = Form(default=None),
    company_name: Optional[str] = Form(default=None),
    role_title: Optional[str] = Form(default=None),
    analysis_mode: str = Form(default="openai"),
    current_user: User = Depends(get_current_user),
) -> CoverLetterResponse:
    resume_text = await _extract_text_or_400(resume)
    cover_letter = generate_cover_letter(
        resume_text=resume_text,
        job_description=job_description,
        company_name=company_name,
        role_title=role_title,
        analysis_mode=analysis_mode,
    )
    return CoverLetterResponse(cover_letter=cover_letter)


@router.post(
    "/generate/interview-questions",
    response_model=InterviewQuestionsResponse,
    dependencies=[Depends(rate_limit_generation)],
)
async def create_interview_questions(
    resume: UploadFile = File(...),
    job_description: Optional[str] = Form(default=None),
    analysis_mode: str = Form(default="openai"),
    current_user: User = Depends(get_current_user),
) -> InterviewQuestionsResponse:
    resume_text = await _extract_text_or_400(resume)
    questions = generate_interview_questions(
        resume_text=resume_text,
        job_description=job_description,
        analysis_mode=analysis_mode,
    )
    return InterviewQuestionsResponse(questions=questions)


@router.post(
    "/generate/rewrite-section",
    response_model=RewriteSectionResponse,
    dependencies=[Depends(rate_limit_generation)],
)
async def rewrite_section(
    resume: UploadFile = File(...),
    section_type: str = Form(default="summary"),
    job_description: Optional[str] = Form(default=None),
    analysis_mode: str = Form(default="openai"),
    current_user: User = Depends(get_current_user),
) -> RewriteSectionResponse:
    normalized_section = section_type.strip().lower()
    if normalized_section not in ALLOWED_REWRITE_SECTIONS:
        allowed = ", ".join(sorted(ALLOWED_REWRITE_SECTIONS))
        raise HTTPException(status_code=400, detail=f"section_type must be one of: {allowed}.")

    resume_text = await _extract_text_or_400(resume)
    result = rewrite_resume_section(
        resume_text=resume_text,
        section_type=normalized_section,
        job_description=job_description,
        analysis_mode=analysis_mode,
    )
    return RewriteSectionResponse(**result)


async def _extract_text_or_400(resume: UploadFile) -> str:
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

    return resume_text
