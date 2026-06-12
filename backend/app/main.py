from __future__ import annotations

import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routes.analyze import router as analyze_router
from app.routes.auth import router as auth_router
from app.routes.export import router as export_router
from app.routes.generate import router as generate_router


ENV = os.getenv("ENV", "development").lower()


def _allowed_origins() -> list[str]:
    origins = os.getenv("FRONTEND_ORIGINS")
    if origins:
        try:
            parsed = json.loads(origins)
        except json.JSONDecodeError:
            return [origin.strip() for origin in origins.split(",") if origin.strip()]

        if isinstance(parsed, list):
            allowed = [str(origin).strip() for origin in parsed if str(origin).strip()]
            _validate_origins(allowed)
            return allowed

    fallback_origin = os.getenv("FRONTEND_ORIGIN")
    if fallback_origin:
        allowed = [fallback_origin]
        _validate_origins(allowed)
        return allowed

    if ENV == "production":
        raise RuntimeError("FRONTEND_ORIGINS must be set when ENV=production.")

    return ["http://localhost:3000"]


def _validate_origins(origins: list[str]) -> None:
    if ENV == "production" and not origins:
        raise RuntimeError("At least one frontend origin must be configured in production.")
    if "*" in origins:
        raise RuntimeError("Wildcard CORS origins are not allowed when credentials are enabled.")


app = FastAPI(
    title="CV Analyzer AI SaaS",
    description="Resume analysis API with ATS scoring and job-fit feedback.",
    version="0.1.0",
    docs_url=None if ENV == "production" else "/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(analyze_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(generate_router, prefix="/api")
@app.get("/")
async def root():
    return {"status": "ok", "message": "CV Analyzer API is running"}

@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
