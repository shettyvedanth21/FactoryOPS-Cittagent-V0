import logging
from typing import Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WebhookAdapter:
    async def send(
        self,
        url: str,
        payload: Dict[str, Any]
    ) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code >= 400:
                    logger.warning(f"Webhook returned non-2xx: {response.status_code}")
                else:
                    logger.info(f"Webhook sent to {url}")
        except httpx.TimeoutException:
            logger.warning(f"Webhook timeout for {url}")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
            raise
