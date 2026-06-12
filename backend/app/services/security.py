from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import HTTPException, Request, status


MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
ALLOWED_RESUME_EXTENSIONS = {".pdf", ".docx", ".txt"}


class InMemoryRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        hits = self._hits[key]
        cutoff = now - self.window_seconds

        while hits and hits[0] < cutoff:
            hits.popleft()

        if len(hits) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait and try again.",
            )

        hits.append(now)


auth_limiter = InMemoryRateLimiter(
    limit=int(os.getenv("AUTH_RATE_LIMIT", "10")),
    window_seconds=int(os.getenv("AUTH_RATE_WINDOW_SECONDS", "60")),
)
analysis_limiter = InMemoryRateLimiter(
    limit=int(os.getenv("ANALYSIS_RATE_LIMIT", "20")),
    window_seconds=int(os.getenv("ANALYSIS_RATE_WINDOW_SECONDS", "3600")),
)
guest_analysis_limiter = InMemoryRateLimiter(
    limit=int(os.getenv("GUEST_ANALYSIS_RATE_LIMIT", "1")),
    window_seconds=int(os.getenv("GUEST_ANALYSIS_RATE_WINDOW_SECONDS", "86400")),
)
generation_limiter = InMemoryRateLimiter(
    limit=int(os.getenv("GENERATION_RATE_LIMIT", "30")),
    window_seconds=int(os.getenv("GENERATION_RATE_WINDOW_SECONDS", "3600")),
)


def rate_limit_auth(request: Request) -> None:
    auth_limiter.check(_client_key(request, "auth"))


def rate_limit_analysis(request: Request, *, user_id: int | None = None) -> None:
    if user_id is not None:
        analysis_limiter.check(f"analysis:user:{user_id}")
        return

    try:
        guest_analysis_limiter.check(_client_key(request, "guest-analysis"))
    except HTTPException as exc:
        exc.detail = "Guest limit reached. Create a free account to run more resume analyses."
        raise exc


def rate_limit_generation(request: Request) -> None:
    generation_limiter.check(_client_key(request, "generation"))


def validate_resume_upload(filename: str, file_bytes: bytes) -> None:
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_RESUME_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_RESUME_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Upload one of: {allowed}.")

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Resume file is too large. Maximum size is {max_mb:.1f} MB.",
        )


def _client_key(request: Request, bucket: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{bucket}:{host}"
