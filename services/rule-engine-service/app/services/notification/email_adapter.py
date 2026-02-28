import logging
import smtplib
from email.mime.text import MIMEText
from typing import List

from app.config import settings

logger = logging.getLogger(__name__)


class EmailAdapter:
    async def send(
        self,
        recipients: List[str],
        subject: str,
        body: str
    ) -> None:
        if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP not configured, skipping email notification")
            return
        
        try:
            msg = MIMEText(body, "plain")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_USER
            msg["To"] = ", ".join(recipients)
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"Email sent to {recipients}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise
