from __future__ import annotations

import unittest

from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas import UserCreate
from app.services.resume_parser import validate_resume_text_content
from app.services import security
from app.services.security import InMemoryRateLimiter, validate_resume_upload


class SecurityTests(unittest.TestCase):
    def test_password_requires_letter_and_number(self) -> None:
        with self.assertRaises(ValidationError):
            UserCreate(email="user@example.com", password="password")

        user = UserCreate(email="user@example.com", password="password1")
        self.assertEqual(user.email, "user@example.com")

    def test_resume_upload_rejects_unsupported_extension(self) -> None:
        with self.assertRaises(HTTPException) as context:
            validate_resume_upload("resume.exe", b"content")

        self.assertEqual(context.exception.status_code, 400)

    def test_rate_limiter_blocks_after_limit(self) -> None:
        limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
        limiter.check("client")
        limiter.check("client")

        with self.assertRaises(HTTPException) as context:
            limiter.check("client")

        self.assertEqual(context.exception.status_code, 429)

    def test_guest_analysis_limit_invites_registration(self) -> None:
        original_limiter = security.guest_analysis_limiter
        security.guest_analysis_limiter = InMemoryRateLimiter(limit=1, window_seconds=60)

        class Request:
            client = type("Client", (), {"host": "127.0.0.1"})()

        try:
            security.rate_limit_analysis(Request())
            with self.assertRaises(HTTPException) as context:
                security.rate_limit_analysis(Request())
        finally:
            security.guest_analysis_limiter = original_limiter

        self.assertEqual(context.exception.status_code, 429)
        self.assertIn("Create a free account", context.exception.detail)

    def test_resume_content_rejects_project_specification(self) -> None:
        text = (
            "Technical specification for CV Analyzer platform. "
            "Functional requirements: upload PDF, analyze text, return score. "
            "Non-functional requirements: Docker deployment, PostgreSQL, API security. "
            "Acceptance criteria: system returns analysis after upload. "
            "Deliverables include frontend, backend, and documentation."
        )

        with self.assertRaises(ValueError):
            validate_resume_text_content(text)

    def test_resume_content_rejects_job_posting(self) -> None:
        text = (
            "Job Description: We are looking for a marketing manager. "
            "Responsibilities include campaign planning, reporting, and vendor management. "
            "Required qualifications: 3 years of experience, Google Analytics, SEO, and CRM. "
            "Benefits include health insurance, paid holidays, and remote work. Apply now."
        )

        with self.assertRaises(ValueError):
            validate_resume_text_content(text)

    def test_resume_content_rejects_invoice(self) -> None:
        text = (
            "Invoice #1024. Payment due within 14 days. "
            "Subtotal 1200 USD. Tax ID 123456789. Total amount 1440 USD. "
            "Purchase order and terms and conditions are listed below. "
            "Signature required by both parties."
        )

        with self.assertRaises(ValueError):
            validate_resume_text_content(text)

    def test_resume_content_accepts_resume(self) -> None:
        text = (
            "David Candidate david@example.com +1 555 123 4567 linkedin.com/in/david. "
            "Summary: Marketing specialist with experience in SEO, content marketing, and analytics. "
            "Experience: 2021-present managed campaigns, improved conversion by 18%, and coordinated vendors. "
            "Education: Bachelor of Business Administration. "
            "Skills: Google Analytics, SEO, copywriting, CRM, project management."
        )

        validate_resume_text_content(text)


if __name__ == "__main__":
    unittest.main()
