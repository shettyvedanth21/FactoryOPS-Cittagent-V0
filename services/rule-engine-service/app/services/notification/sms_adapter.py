import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class SMSAdapter:
    def __init__(self):
        self._client: Optional[Any] = None
    
    def _get_client(self):
        if self._client is None:
            if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
                return None
            self._client = boto3.client(
                "sns",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return self._client
    
    async def send(
        self,
        phone_number: str,
        message: str
    ) -> None:
        client = self._get_client()
        if not client:
            logger.warning("AWS SNS not configured, skipping SMS notification")
            return
        
        try:
            client.publish(
                PhoneNumber=phone_number,
                Message=message
            )
            logger.info(f"SMS sent to {phone_number}")
        except ClientError as e:
            logger.error(f"Failed to send SMS: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            raise
