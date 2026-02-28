import logging
from typing import Optional

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.config import settings

logger = logging.getLogger(__name__)


class WhatsAppAdapter:
    def __init__(self):
        self._client: Optional[Client] = None
    
    def _get_client(self) -> Optional[Client]:
        if self._client is None:
            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                return None
            self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        return self._client
    
    async def send(
        self,
        phone_number: str,
        message: str
    ) -> None:
        client = self._get_client()
        if not client:
            logger.warning("Twilio not configured, skipping WhatsApp notification")
            return
        
        try:
            from_whatsapp = settings.TWILIO_WHATSAPP_FROM
            if not from_whatsapp:
                logger.warning("Twilio WhatsApp FROM number not configured")
                return
            
            client.messages.create(
                body=message,
                from_=from_whatsapp,
                to=f"whatsapp:{phone_number}"
            )
            logger.info(f"WhatsApp sent to {phone_number}")
        except TwilioRestException as e:
            logger.error(f"Failed to send WhatsApp: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send WhatsApp: {e}")
            raise
