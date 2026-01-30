"""Gmail SMTP email sender with rate limiting."""

from __future__ import annotations

import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from job_automator.config.settings import get_settings
from job_automator.db.repository import count_emails_sent_today


class EmailSender:
    """Send emails via SMTP with rate limiting."""

    def __init__(self):
        settings = get_settings()
        self.smtp_host = settings.email.smtp_host
        self.smtp_port = settings.email.smtp_port
        self.sender_email = settings.email.sender_email
        self.sender_password = settings.email.sender_password
        self.daily_limit = settings.email.daily_limit
        self.delay = settings.email.delay_between_sends

    def can_send(self) -> tuple[bool, str]:
        """Check if we can send another email today."""
        if not self.sender_email or not self.sender_password:
            return False, "Email not configured. Set sender_email and sender_password in config.yaml"

        sent_today = count_emails_sent_today()
        if sent_today >= self.daily_limit:
            return False, f"Daily limit reached ({sent_today}/{self.daily_limit})"

        return True, ""

    def send(
        self,
        to_email: str,
        subject: str,
        body: str,
        reply_to: str = "",
    ) -> bool:
        """Send a single email. Returns True on success."""
        can, reason = self.can_send()
        if not can:
            raise RuntimeError(reason)

        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = to_email
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)

        return True

    def send_with_delay(self):
        """Wait for the configured delay between sends."""
        time.sleep(self.delay)
