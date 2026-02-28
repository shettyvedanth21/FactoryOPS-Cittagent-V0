import logging
from typing import Dict, Any
import httpx

from src.config import settings


logger = logging.getLogger(__name__)


async def trigger_rule_evaluation(device_id: str, telemetry: Dict[str, Any]):
    """
    Trigger rule evaluation via HTTP POST to rule-engine service.
    
    Non-blocking, 2 second timeout.
    """
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            payload = {
                "device_id": device_id,
                "telemetry": telemetry
            }
            
            response = await client.post(
                f"{settings.RULE_ENGINE_URL}/api/v1/rules/evaluate",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Rule evaluation triggered for device {device_id}")
            else:
                logger.warning(
                    f"Rule evaluation failed for {device_id}: {response.status_code}"
                )
    
    except httpx.TimeoutException:
        logger.warning(f"Rule evaluation timeout for device {device_id}")
    except Exception as e:
        logger.warning(f"Rule evaluation error for device {device_id}: {str(e)}")
