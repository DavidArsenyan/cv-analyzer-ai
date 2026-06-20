from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas import (
    AuthResponse,
    EmailVerificationRequest,
    ForgotPasswordRequest,
    ResendVerificationRequest,
    ResetPasswordRequest,
    UserCreate,
    UserResponse,
    VerificationRequiredResponse,
)
from app.services.auth import (
    authenticate_user,
    cleanup_expired_unverified_users,
    create_access_token,
    create_email_verification_code,
    create_password_reset_code,
    create_user,
    delete_user,
    get_current_user,
    get_user_by_email,
    is_email_verification_expired,
    reset_password_with_code,
    verify_email_code,
)
from app.services.email import send_password_reset_email, send_verification_email
from app.services.security import rate_limit_auth


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=VerificationRequiredResponse, dependencies=[Depends(rate_limit_auth)])
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> VerificationRequiredResponse:
    cleanup_expired_unverified_users(db)
    existing_user = get_user_by_email(db, payload.email)
    if existing_user:
        if existing_user.is_email_verified:
            raise HTTPException(status_code=409, detail="Email is already registered.")
        delete_user(db, existing_user)

    user = create_user(db=db, email=payload.email, password=payload.password)
    code = create_email_verification_code(db=db, user=user)
    try:
        send_verification_email(user.email, code)
    except Exception as exc:
        delete_user(db, user)
        print(f"Email verification send failed: {exc}", flush=True)
        raise HTTPException(status_code=500, detail="Could not send verification email.") from exc

    return VerificationRequiredResponse(email=user.email, detail="Verification code sent.")


@router.post("/verify-email", response_model=AuthResponse, dependencies=[Depends(rate_limit_auth)])
def verify_email(payload: EmailVerificationRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = get_user_by_email(db, payload.email)
    if not user or not verify_email_code(db=db, user=user, code=payload.code):
        if user and not user.is_email_verified and is_email_verification_expired(user):
            delete_user(db, user)
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    return AuthResponse(access_token=create_access_token(user), user=UserResponse.from_user(user))


@router.post("/resend-verification", response_model=VerificationRequiredResponse, dependencies=[Depends(rate_limit_auth)])
def resend_verification(
    payload: ResendVerificationRequest,
    db: Session = Depends(get_db),
) -> VerificationRequiredResponse:
    cleanup_expired_unverified_users(db)
    user = get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(status_code=404, detail="Email is not registered.")
    if user.is_email_verified:
        return VerificationRequiredResponse(email=user.email, detail="Email is already verified.")

    code = create_email_verification_code(db=db, user=user)
    try:
        send_verification_email(user.email, code)
    except Exception as exc:
        print(f"Email verification resend failed: {exc}", flush=True)
        raise HTTPException(status_code=500, detail="Could not send verification email.") from exc

    return VerificationRequiredResponse(email=user.email, detail="Verification code sent.")


@router.post("/forgot-password", response_model=VerificationRequiredResponse, dependencies=[Depends(rate_limit_auth)])
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> VerificationRequiredResponse:
    cleanup_expired_unverified_users(db)
    user = get_user_by_email(db, payload.email)
    if not user or not user.is_email_verified:
        return VerificationRequiredResponse(email=payload.email, detail="If that email is registered, a reset code was sent.")

    code = create_password_reset_code(db=db, user=user)
    try:
        send_password_reset_email(user.email, code)
    except Exception as exc:
        print(f"Password reset email send failed: {exc}", flush=True)
        raise HTTPException(status_code=500, detail="Could not send password reset email.") from exc

    return VerificationRequiredResponse(email=user.email, detail="Password reset code sent.")


@router.post("/reset-password", response_model=AuthResponse, dependencies=[Depends(rate_limit_auth)])
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> AuthResponse:
    cleanup_expired_unverified_users(db)
    user = get_user_by_email(db, payload.email)
    if not user or not user.is_email_verified:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code.")
    if not reset_password_with_code(db=db, user=user, code=payload.code, password=payload.password):
        raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

    return AuthResponse(access_token=create_access_token(user), user=UserResponse.from_user(user))


@router.post("/login", response_model=AuthResponse, dependencies=[Depends(rate_limit_auth)])
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> AuthResponse:
    cleanup_expired_unverified_users(db)
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
