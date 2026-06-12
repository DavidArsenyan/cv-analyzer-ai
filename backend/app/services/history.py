from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.analysis_record import AnalysisRecord
from app.schemas import AnalysisHistoryItem, ResumeAnalysisResponse


def save_analysis_record(
    db: Session,
    user_id: int,
    filename: str,
    result: ResumeAnalysisResponse,
    target_role: str | None = None,
) -> AnalysisRecord:
    record = AnalysisRecord(
        user_id=user_id,
        filename=filename,
        target_role=target_role,
        analysis_mode=result.analysis_mode,
        ats_score=result.ats_score,
        job_match_score=result.job_match_score,
        result_json=result.model_dump_json(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_analysis_records(db: Session, limit: int = 10) -> list[AnalysisHistoryItem]:
    raise NotImplementedError("Use list_user_analysis_records instead.")


def list_user_analysis_records(db: Session, user_id: int, limit: int = 10) -> list[AnalysisHistoryItem]:
    statement = (
        select(AnalysisRecord)
        .where(AnalysisRecord.user_id == user_id)
        .order_by(AnalysisRecord.created_at.desc(), AnalysisRecord.id.desc())
        .limit(limit)
    )
    records = db.scalars(statement).all()

    return [
        AnalysisHistoryItem(
            id=record.id,
            filename=record.filename,
            target_role=record.target_role,
            analysis_mode=record.analysis_mode,
            ats_score=record.ats_score,
            job_match_score=record.job_match_score,
            created_at=record.created_at.isoformat(),
            detected_skills=json.loads(record.result_json).get("detected_skills", []),
        )
        for record in records
    ]
