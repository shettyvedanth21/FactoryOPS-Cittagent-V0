import logging
from typing import Dict, Any
import httpx

from src.config import settings


logger = logging.getLogger(__name__)


async def discover_device_properties(device_id: str, telemetry: Dict[str, Any]):
    """
    Auto-discover device properties from telemetry and upsert to device-service.
    
    Calls device-service API to create/update properties.
    """
    for property_name, value in telemetry.items():
        if not isinstance(value, (int, float)):
            continue
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                payload = {
                    "property_name": property_name,
                    "data_type": "float",
                    "is_numeric": True
                }
                
                response = await client.post(
                    f"{settings.DEVICE_SERVICE_URL}/api/v1/devices/{device_id}/properties",
                    json=payload
                )
                
                if response.status_code in (200, 201):
                    logger.debug(f"Discovered property {property_name} for device {device_id}")
        
        except Exception as e:
            logger.warning(f"Failed to discover property {property_name} for {device_id}: {str(e)}")
