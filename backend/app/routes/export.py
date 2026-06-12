from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.models.user import User
from app.schemas import ExportReportRequest
from app.services.auth import get_current_user
from app.services.pdf_export import build_analysis_pdf
from app.services.security import rate_limit_generation


router = APIRouter(prefix="/export", tags=["export"])


@router.post("/report", dependencies=[Depends(rate_limit_generation)])
def export_report(
    payload: ExportReportRequest,
    current_user: User = Depends(get_current_user),
) -> Response:
    pdf_bytes = build_analysis_pdf(payload)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="cv-analysis-report-{timestamp}.pdf"'},
    )
