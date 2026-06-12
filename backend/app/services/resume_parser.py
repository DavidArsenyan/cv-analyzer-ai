import os
import re
from io import BytesIO
from pathlib import Path


MAX_PDF_PAGES = int(os.getenv("MAX_PDF_PAGES", "30"))
RESUME_TEXT_MIN_LENGTH = 80


def extract_resume_text(filename: str, file_bytes: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return _extract_pdf_text(file_bytes)
    if extension == ".docx":
        return _extract_docx_text(file_bytes)
    if extension == ".txt":
        return _extract_txt_text(file_bytes)

    raise ValueError("Unsupported file type. Upload PDF, DOCX, or TXT.")


def validate_resume_text_content(resume_text: str) -> None:
    normalized_text = re.sub(r"\s+", " ", resume_text.lower()).strip()
    if len(normalized_text) < RESUME_TEXT_MIN_LENGTH:
        raise ValueError("Could not extract enough text from the resume.")

    resume_score = _resume_evidence_score(normalized_text)
    non_resume_score = _non_resume_evidence_score(normalized_text)

    if resume_score < 3:
        raise ValueError("The uploaded file does not look like a resume or CV.")
    if non_resume_score >= 3 and resume_score < 5:
        raise ValueError("The uploaded file looks like a non-resume document. Please upload a resume or CV.")


def _resume_evidence_score(text: str) -> int:
    score = 0

    contact_matches = 0
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        contact_matches += 1
    if re.search(r"(?:\+?\d[\d\s().-]{7,}\d)", text):
        contact_matches += 1
    if re.search(r"\b(?:linkedin|github|portfolio|website)\b", text):
        contact_matches += 1
    score += min(contact_matches, 2)

    section_patterns = (
        r"\b(?:experience|employment|work history|professional experience)\b",
        r"\b(?:education|academic background|degree|university|college)\b",
        r"\b(?:skills|technical skills|core competencies|competencies)\b",
        r"\b(?:projects|certifications|certificates|summary|profile|languages)\b",
        r"(?:\u043e\u043f\u044b\u0442\s+\u0440\u0430\u0431\u043e\u0442\u044b|\u043e\u0431\u0440\u0430\u0437\u043e\u0432\u0430\u043d\u0438\u0435|\u043d\u0430\u0432\u044b\u043a\u0438|\u043f\u0440\u043e\u0435\u043a\u0442\u044b|\u0441\u0435\u0440\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u044b|\u0440\u0435\u0437\u044e\u043c\u0435|\u043f\u0440\u043e\u0444\u0438\u043b\u044c|\u044f\u0437\u044b\u043a\u0438)",
    )
    score += min(sum(1 for pattern in section_patterns if re.search(pattern, text)), 3)

    if re.search(
        r"\b(?:developer|engineer|manager|analyst|designer|marketer|translator|accountant|consultant|specialist|assistant|coordinator|director|officer|administrator)\b",
        text,
    ):
        score += 1
    if re.search(r"\b(?:19|20)\d{2}\s*(?:-|\u2013|to|present|current|now)", text):
        score += 1
    if re.search(
        r"\b(?:built|created|managed|led|developed|implemented|improved|increased|reduced|translated|designed|analyzed|coordinated)\b",
        text,
    ):
        score += 1
    if re.search(r"\b(?:bachelor|master|phd|mba|b\.s\.|m\.s\.|certified|certification)\b", text):
        score += 1

    return score


def _non_resume_evidence_score(text: str) -> int:
    patterns = (
        r"\b(?:technical specification|terms of reference|statement of work|scope of work|functional requirements|non-functional requirements|acceptance criteria|deliverables|system requirements)\b",
        r"(?:\u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u043e\u0435\s+\u0437\u0430\u0434\u0430\u043d\u0438\u0435|\u0444\u0443\u043d\u043a\u0446\u0438\u043e\u043d\u0430\u043b\u044c\u043d\u044b\u0435\s+\u0442\u0440\u0435\u0431\u043e\u0432\u0430\u043d\u0438\u044f|\u043a\u0440\u0438\u0442\u0435\u0440\u0438\u0438\s+\u043f\u0440\u0438(?:\u0435|\u0451)\u043c\u043a\u0438|\u0437\u0430\u043a\u0430\u0437\u0447\u0438\u043a|\u0438\u0441\u043f\u043e\u043b\u043d\u0438\u0442\u0435\u043b\u044c)",
        r"\b(?:job description|we are looking for|responsibilities include|required qualifications|preferred qualifications|salary|benefits|apply now|job type)\b",
        r"\b(?:invoice|receipt|payment due|subtotal|total amount|tax id|purchase order)\b",
        r"\b(?:agreement|contract|party agrees|terms and conditions|signature|whereas)\b",
        r"\b(?:abstract|introduction|methodology|literature review|references|bibliography|appendix)\b",
        r"\b(?:meeting minutes|agenda|minutes of meeting|action items)\b",
    )
    score = sum(1 for pattern in patterns if re.search(pattern, text))

    if re.search(r"\b(?:requirements|responsibilities|deliverables)\b", text) and not re.search(
        r"\b(?:experience|education|skills|employment|summary|profile)\b",
        text,
    ):
        score += 1

    return score


def _extract_pdf_text(file_bytes: bytes) -> str:
    import fitz

    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except fitz.FileDataError as exc:
        raise ValueError("The uploaded PDF could not be read. Please upload a valid text-based PDF, DOCX, or TXT resume.") from exc
    except fitz.EmptyFileError as exc:
        raise ValueError("The uploaded PDF is empty.") from exc
    try:
        if document.page_count > MAX_PDF_PAGES:
            raise ValueError(f"PDF has too many pages. Maximum is {MAX_PDF_PAGES}.")
        pages = [page.get_text("text") for page in document]
        text = "\n".join(pages)
        if len(text.strip()) < 50:
            raise ValueError(
                "The PDF appears to be scanned or image-based. Please upload a text-based PDF, DOCX, or TXT resume."
            )
        return text
    finally:
        document.close()


def _extract_docx_text(file_bytes: bytes) -> str:
    from docx import Document

    try:
        document = Document(BytesIO(file_bytes))
    except Exception as exc:
        raise ValueError("The uploaded DOCX could not be read. Please upload a valid resume.") from exc

    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs)


def _extract_txt_text(file_bytes: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("Could not read the text file encoding.")
