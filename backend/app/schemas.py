from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import User


class SkillGap(BaseModel):
    skill: str
    reason: str


class ResumeAnalysisResponse(BaseModel):
    analysis_mode: str = "local"
    fallback_notice: Optional[str] = None
    ats_score: int = Field(ge=0, le=100)
    job_match_score: Optional[int] = Field(default=None, ge=0, le=100)
    detected_skills: list[str]
    missing_skills: list[SkillGap]
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    improved_summary: str


class ExportReportRequest(BaseModel):
    analysis: ResumeAnalysisResponse
    cover_letter: Optional[str] = None
    rewritten_section: Optional[str] = None


class CoverLetterResponse(BaseModel):
    cover_letter: str


class InterviewQuestionsResponse(BaseModel):
    questions: list[str]


class RewriteSectionResponse(BaseModel):
    section_type: str
    rewritten_section: str
    improvement_notes: list[str]


class AnalysisHistoryItem(BaseModel):
    id: int
    filename: str
    target_role: Optional[str] = None
    analysis_mode: str
    ats_score: int
    job_match_score: Optional[int] = None
    created_at: str
    detected_skills: list[str]


class PasswordMixin(BaseModel):
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        has_letter = any(character.isalpha() for character in value)
        has_digit = any(character.isdigit() for character in value)
        if not has_letter or not has_digit:
            raise ValueError("Password must contain at least one letter and one number.")
        return value


class UserCreate(PasswordMixin):
    email: EmailStr


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_email_verified: bool

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(id=user.id, email=user.email, is_email_verified=user.is_email_verified)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class VerificationRequiredResponse(BaseModel):
    email: EmailStr
    detail: str


class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Verification code must contain digits only.")
        return value


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(PasswordMixin):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Reset code must contain digits only.")
        return value
