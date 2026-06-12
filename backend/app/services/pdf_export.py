from __future__ import annotations

from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from app.schemas import ExportReportRequest


def build_analysis_pdf(payload: ExportReportRequest) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=42,
        bottomMargin=42,
        title="CV Analysis Report",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#0f766e"),
            spaceBefore=14,
            spaceAfter=8,
        )
    )
    story = []
    analysis = payload.analysis

    story.append(Paragraph("CV Analysis Report", styles["Title"]))
    story.append(Paragraph(f"Analysis mode: {analysis.analysis_mode.upper()}", styles["Normal"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Scores", styles["SectionTitle"]))
    story.append(Paragraph(f"ATS Score: <b>{analysis.ats_score}%</b>", styles["Normal"]))
    job_match = "N/A" if analysis.job_match_score is None else f"{analysis.job_match_score}%"
    story.append(Paragraph(f"Job Match Score: <b>{job_match}</b>", styles["Normal"]))

    _add_list(story, styles, "Detected Skills", analysis.detected_skills)
    _add_list(story, styles, "Missing Skills", [f"{gap.skill}: {gap.reason}" for gap in analysis.missing_skills])
    _add_list(story, styles, "Strengths", analysis.strengths)
    _add_list(story, styles, "Weaknesses", analysis.weaknesses)
    _add_list(story, styles, "Recommendations", analysis.recommendations)

    story.append(Paragraph("Improved Summary", styles["SectionTitle"]))
    story.append(Paragraph(_escape(analysis.improved_summary), styles["BodyText"]))

    if payload.rewritten_section:
        story.append(Paragraph("Rewritten Section", styles["SectionTitle"]))
        story.append(Paragraph(_escape(payload.rewritten_section), styles["BodyText"]))

    if payload.cover_letter:
        story.append(Paragraph("Cover Letter Draft", styles["SectionTitle"]))
        story.append(Paragraph(_escape(payload.cover_letter).replace("\n", "<br/>"), styles["BodyText"]))

    document.build(story)
    return buffer.getvalue()


def _add_list(story: list, styles, title: str, items: list[str]) -> None:
    story.append(Paragraph(title, styles["SectionTitle"]))
    if not items:
        story.append(Paragraph("None", styles["BodyText"]))
        return

    for item in items:
        story.append(Paragraph(f"- {_escape(item)}", styles["BodyText"]))


def _escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
