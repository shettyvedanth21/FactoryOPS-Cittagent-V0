import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class TelegramAdapter:
    async def send(
        self,
        chat_id: str,
        message: str
    ) -> None:
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram bot token not configured, skipping notification")
            return
        
        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code >= 400:
                    logger.warning(f"Telegram API returned: {response.status_code}")
                else:
                    logger.info(f"Telegram message sent to {chat_id}")
        except httpx.TimeoutException:
            logger.warning(f"Telegram request timeout for {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            raise
