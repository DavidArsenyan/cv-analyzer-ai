# from __future__ import annotations
#
# import os
# import smtplib
# from email.message import EmailMessage
#
#
# ENV = os.getenv("ENV", "development").lower()
# SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
# SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
# SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
# SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
# SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME).strip()
# SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CV Analyzer AI").strip()
# SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
#
#
# def send_verification_email(recipient_email: str, code: str) -> None:
#     if not SMTP_HOST:
#         if ENV == "production":
#             raise RuntimeError("SMTP_HOST must be set when ENV=production.")
#         print(f"[dev] Email verification code for {recipient_email}: {code}")
#         return
#
#     if not SMTP_FROM_EMAIL:
#         raise RuntimeError("SMTP_FROM_EMAIL or SMTP_USERNAME must be set.")
#
#     message = EmailMessage()
#     message["Subject"] = "Your CV Analyzer AI verification code"
#     message["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
#     message["To"] = recipient_email
#     message.set_content(
#         "\n".join(
#             [
#                 "Your CV Analyzer AI verification code is:",
#                 "",
#                 code,
#                 "",
#                 "This code expires in 15 minutes.",
#                 "If you did not request this account, you can ignore this email.",
#             ]
#         )
#     )
#
#     with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as smtp:
#         if SMTP_USE_TLS:
#             smtp.starttls()
#         if SMTP_USERNAME and SMTP_PASSWORD:
#             smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
#         smtp.send_message(message)
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

ENV = os.getenv("ENV", "development").lower()
SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))  # Defaulting to 465 for cloud environments
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USERNAME).strip()
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "CV Analyzer AI").strip()
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "false").lower() == "true"


def send_verification_email(recipient_email: str, code: str) -> None:
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
    message.set_content(
        "\n".join(
            [
                "Your CV Analyzer AI verification code is:",
                "",
                code,
                "",
                "This code expires in 15 minutes.",
                "If you did not request this account, you can ignore this email.",
            ]
        )
    )

    # Dynamically select the correct connection method based on the port
    if SMTP_PORT == 465:
        # Port 465 requires SSL from the very start
        smtp_client = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=15)
    else:
        # Port 587 or others start unencrypted
        smtp_client = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15)

    with smtp_client as smtp:
        # Only issue STARTTLS if we are NOT on port 465 and TLS is requested
        if SMTP_PORT != 465 and SMTP_USE_TLS:
            smtp.starttls()

        if SMTP_USERNAME and SMTP_PASSWORD:
            smtp.login(SMTP_USERNAME, SMTP_PASSWORD)

        smtp.send_message(message)
