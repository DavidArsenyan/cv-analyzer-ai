from __future__ import annotations

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User


load_dotenv()

ENV = os.getenv("ENV", "development").lower()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    if ENV == "production":
        raise RuntimeError("JWT_SECRET_KEY must be set when ENV=production.")
    JWT_SECRET_KEY = "change-this-secret-in-production"
if ENV == "production" and (
    JWT_SECRET_KEY in {"change-this-secret-in-production", "local-dev-secret-at-least-32-chars"}
    or len(JWT_SECRET_KEY) < 32
):
    raise RuntimeError("JWT_SECRET_KEY must be a strong production secret.")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
EMAIL_VERIFICATION_EXPIRE_MINUTES = int(os.getenv("EMAIL_VERIFICATION_EXPIRE_MINUTES", "15"))
EMAIL_VERIFICATION_MAX_ATTEMPTS = int(os.getenv("EMAIL_VERIFICATION_MAX_ATTEMPTS", "5"))
PASSWORD_RESET_EXPIRE_MINUTES = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15"))
PASSWORD_RESET_MAX_ATTEMPTS = int(os.getenv("PASSWORD_RESET_MAX_ATTEMPTS", "5"))

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_context.verify(password, hashed_password)


def create_access_token(user: User) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user.id), "email": user.email, "exp": expires_at}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    statement = select(User).where(User.email == email.lower())
    return db.scalars(statement).first()


def create_user(db: Session, email: str, password: str, *, is_email_verified: bool = False) -> User:
    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        is_email_verified=is_email_verified,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_email_verification_code(db: Session, user: User) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.email_verification_code_hash = hash_password(code)
    now = _utcnow_naive()
    user.email_verification_expires_at = now + timedelta(minutes=EMAIL_VERIFICATION_EXPIRE_MINUTES)
    user.email_verification_attempts = 0
    user.email_verification_sent_at = now
    db.add(user)
    db.commit()
    db.refresh(user)
    return code


def delete_user(db: Session, user: User) -> None:
    db.delete(user)
    db.commit()


def cleanup_expired_unverified_users(db: Session) -> None:
    now = _utcnow_naive()
    statement = delete(User).where(
        User.is_email_verified.is_(False),
        User.email_verification_expires_at.is_not(None),
        User.email_verification_expires_at < now,
    )
    db.execute(statement)
    db.commit()


def is_email_verification_expired(user: User) -> bool:
    return bool(user.email_verification_expires_at and _utcnow_naive() > user.email_verification_expires_at)


def verify_email_code(db: Session, user: User, code: str) -> bool:
    if user.is_email_verified:
        return True
    if not user.email_verification_code_hash or not user.email_verification_expires_at:
        return False
    if user.email_verification_attempts >= EMAIL_VERIFICATION_MAX_ATTEMPTS:
        return False
    if _utcnow_naive() > user.email_verification_expires_at:
        return False

    user.email_verification_attempts += 1
    if not verify_password(code, user.email_verification_code_hash):
        db.add(user)
        db.commit()
        return False

    user.is_email_verified = True
    user.email_verification_code_hash = None
    user.email_verification_expires_at = None
    user.email_verification_attempts = 0
    user.email_verification_sent_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return True


def create_password_reset_code(db: Session, user: User) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    user.password_reset_code_hash = hash_password(code)
    now = _utcnow_naive()
    user.password_reset_expires_at = now + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    user.password_reset_attempts = 0
    user.password_reset_sent_at = now
    db.add(user)
    db.commit()
    db.refresh(user)
    return code


def reset_password_with_code(db: Session, user: User, code: str, password: str) -> bool:
    if not user.password_reset_code_hash or not user.password_reset_expires_at:
        return False
    if user.password_reset_attempts >= PASSWORD_RESET_MAX_ATTEMPTS:
        return False
    if _utcnow_naive() > user.password_reset_expires_at:
        return False

    user.password_reset_attempts += 1
    if not verify_password(code, user.password_reset_code_hash):
        db.add(user)
        db.commit()
        return False

    user.hashed_password = hash_password(password)
    user.password_reset_code_hash = None
    user.password_reset_expires_at = None
    user.password_reset_attempts = 0
    user.password_reset_sent_at = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return True


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if not user:
        raise credentials_exception

    return user


def get_optional_user(
    token: Optional[str] = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not token:
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None

    return db.get(User, user_id)
