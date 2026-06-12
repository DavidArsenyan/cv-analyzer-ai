from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas import (
    AuthResponse,
    EmailVerificationRequest,
    ResendVerificationRequest,
    UserCreate,
    UserResponse,
    VerificationRequiredResponse,
)
from app.services.auth import (
    authenticate_user,
    create_access_token,
    create_email_verification_code,
    create_user,
    get_current_user,
    get_user_by_email,
    verify_email_code,
)
from app.services.email import send_verification_email
from app.services.security import rate_limit_auth


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=VerificationRequiredResponse, dependencies=[Depends(rate_limit_auth)])
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> VerificationRequiredResponse:
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="Email is already registered.")

    user = create_user(db=db, email=payload.email, password=payload.password)
    code = create_email_verification_code(db=db, user=user)
    try:
        send_verification_email(user.email, code)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return VerificationRequiredResponse(email=user.email, detail="Verification code sent.")


@router.post("/verify-email", response_model=AuthResponse, dependencies=[Depends(rate_limit_auth)])
def verify_email(payload: EmailVerificationRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = get_user_by_email(db, payload.email)
    if not user or not verify_email_code(db=db, user=user, code=payload.code):
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    return AuthResponse(access_token=create_access_token(user), user=UserResponse.from_user(user))


@router.post("/resend-verification", response_model=VerificationRequiredResponse, dependencies=[Depends(rate_limit_auth)])
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> VerificationRequiredResponse:
    user = get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email is not registered.")
    if user.is_email_verified:
        return VerificationRequiredResponse(email=user.email, detail="Email is already verified.")

    code = create_email_verification_code(db=db, user=user)
    try:
        send_verification_email(user.email, code)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return VerificationRequiredResponse(email=user.email, detail="Verification code sent.")


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(rate_limit_auth)])
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> AuthResponse:
    user = authenticate_user(db=db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email is not verified.")

    return AuthResponse(access_token=create_access_token(user), user=UserResponse.from_user(user))


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.from_user(current_user)
