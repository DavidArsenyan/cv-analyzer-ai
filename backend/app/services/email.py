from __future__ import annotations

import json
import os
import smtplib
import urllib.error
import urllib.request
from email.message import EmailMessage

ENV = os.getenv("ENV", "development").lower()
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp").strip().lower()
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME).strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CV Analyzer AI").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
EMAIL_TIMEOUT_SECONDS = int(os.getenv("EMAIL_TIMEOUT_SECONDS", "15"))


def _verification_text(code: str) -> str:
    return "\n".join(
        [
            "Your CV Analyzer AI verification code is:",
            "",
            code,
            "",
            "This code expires in 15 minutes.",
            "If you did not request this account, you can ignore this email.",
        ]
    )


def _verification_html(code: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; color: #111827; line-height: 1.5;">
      <h2>Your CV Analyzer AI verification code</h2>
      <p>Use this code to verify your email address:</p>
      <p style="font-size: 28px; font-weight: 700; letter-spacing: 4px;">{code}</p>
      <p>This code expires in 15 minutes.</p>
      <p style="color: #6b7280;">If you did not request this account, you can ignore this email.</p>
    </div>
    """.strip()


def send_verification_email(recipient_email: str, code: str) -> None:
    if EMAIL_PROVIDER == "resend":
        _send_with_resend_api(recipient_email, code)
        return

    if not SMTP_HOST:
        if ENV == "production":
            raise RuntimeError("SMTP_HOST must be set when ENV=production.")
        print(f"[dev] Email verification code for {recipient_email}: {code}")
        return

    if not SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP_FROM_EMAIL or SMTP_USERNAME must be set.")

    message = EmailMessage()
    message["Subject"] = "Your CV Analyzer AI verification code"
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = recipient_email
    message.set_content(_verification_text(code))
    message.add_alternative(_verification_html(code), subtype="html")

    if SMTP_PORT == 465:
        smtp_client = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=EMAIL_TIMEOUT_SECONDS)
    else:
        smtp_client = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=EMAIL_TIMEOUT_SECONDS)

    with smtp_client as smtp:
        if SMTP_PORT != 465 and SMTP_USE_TLS:
            smtp.starttls()

        if SMTP_USERNAME and SMTP_PASSWORD:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)

        smtp.send_message(message)


def _send_with_resend_api(recipient_email: str, code: str) -> None:
    api_key = RESEND_API_KEY or SMTP_PASSWORD
    if not api_key:
        raise RuntimeError("RESEND_API_KEY must be set when EMAIL_PROVIDER=resend.")
    if not SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP_FROM_EMAIL must be set when EMAIL_PROVIDER=resend.")

    payload = {
        "from": f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>",
        "to": [recipient_email],
        "subject": "Your CV Analyzer AI verification code",
        "text": _verification_text(code),
        "html": _verification_html(code),
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=EMAIL_TIMEOUT_SECONDS) as response:
            if response.status >= 400:
                body = response.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"Resend API failed with status {response.status}: {body}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend API failed with status {exc.code}: {body}") from exc
