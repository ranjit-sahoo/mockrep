"""Tiny SMTP mailer using only the standard library.

Zero-cost by default: unless SMTP_HOST is set the mailer is disabled and the
app treats email verification as not required (self-hosters without mail keep
working). Any free SMTP relay works (Brevo free tier, Gmail app password, ...):

  SMTP_HOST=smtp-relay.brevo.com SMTP_PORT=587 SMTP_USER=... SMTP_PASS=...
  SMTP_FROM="MockRep <noreply@example.com>"
"""
import os
import smtplib
import ssl
from email.message import EmailMessage

HOST = os.environ.get("SMTP_HOST", "")
PORT = int(os.environ.get("SMTP_PORT", "587"))
USER = os.environ.get("SMTP_USER", "")
PASSWORD = os.environ.get("SMTP_PASS", "")
FROM = os.environ.get("SMTP_FROM", USER or "noreply@localhost")


def enabled() -> bool:
    return bool(HOST)


def send(to: str, subject: str, text: str) -> None:
    if not enabled():
        raise RuntimeError("mail not configured")
    msg = EmailMessage()
    msg["From"] = FROM
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    ctx = ssl.create_default_context()
    with smtplib.SMTP(HOST, PORT, timeout=15) as s:
        s.starttls(context=ctx)
        if USER:
            s.login(USER, PASSWORD)
        s.send_message(msg)
