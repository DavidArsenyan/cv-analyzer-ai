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


def _code_text(code: str, *, action: str, ignore_text: str) -> str:
    return "\n".join(
        [
            f"Your CV Analyzer AI {action} code is:",
            "",
            code,
            "",
            "This code expires in 15 minutes.",
            ignore_text,
        ]
    )


def _code_html(code: str, *, title: str, body: str, ignore_text: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; color: #111827; line-height: 1.5;">
      <h2>{title}</h2>
      <p>{body}</p>
      <p style="font-size: 28px; font-weight: 700; letter-spacing: 4px;">{code}</p>
      <p>This code expires in 15 minutes.</p>
      <p style="color: #6b7280;">{ignore_text}</p>
    </div>
    """.strip()


def send_verification_email(recipient_email: str, code: str) -> None:
    _send_code_email(
        recipient_email=recipient_email,
        code=code,
        subject="Your CV Analyzer AI verification code",
        action="verification",
        title="Your CV Analyzer AI verification code",
        body="Use this code to verify your email address:",
        ignore_text="If you did not request this account, you can ignore this email.",
    )


def send_password_reset_email(recipient_email: str, code: str) -> None:
    _send_code_email(
        recipient_email=recipient_email,
        code=code,
        subject="Your CV Analyzer AI password reset code",
        action="password reset",
        title="Your CV Analyzer AI password reset code",
        body="Use this code to reset your password:",
        ignore_text="If you did not request a password reset, you can ignore this email.",
    )


def _send_code_email(
    *,
    recipient_email: str,
    code: str,
    subject: str,
    action: str,
    title: str,
    body: str,
    ignore_text: str,
) -> None:
    if EMAIL_PROVIDER == "resend":
        _send_with_resend_api(
            recipient_email=recipient_email,
            code=code,
            subject=subject,
            action=action,
            title=title,
            body=body,
            ignore_text=ignore_text,
        )
        return

    if not SMTP_HOST:
        if ENV == "production":
            raise RuntimeError("SMTP_HOST must be set when ENV=production.")
        print(f"[dev] Email {action} code for {recipient_email}: {code}")
        return

    if not SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP_FROM_EMAIL or SMTP_USERNAME must be set.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    message["To"] = recipient_email
    message.set_content(_code_text(code, action=action, ignore_text=ignore_text))
    message.add_alternative(_code_html(code, title=title, body=body, ignore_text=ignore_text), subtype="html")

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


def _send_with_resend_api(
    *,
    recipient_email: str,
    code: str,
    subject: str,
    action: str,
    title: str,
    body: str,
    ignore_text: str,
) -> None:
    api_key = RESEND_API_KEY or SMTP_PASSWORD
    if not api_key:
        raise RuntimeError("RESEND_API_KEY must be set when EMAIL_PROVIDER=resend.")
    if not SMTP_FROM_EMAIL:
        raise RuntimeError("SMTP_FROM_EMAIL must be set when EMAIL_PROVIDER=resend.")

    payload = {
        "from": f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>",
        "to": [recipient_email],
        "subject": subject,
        "text": _code_text(code, action=action, ignore_text=ignore_text),
        "html": _code_html(code, title=title, body=body, ignore_text=ignore_text),
    }
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CV Analyzer AI/1.0 (https://cvanalyzerai.com)",
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
