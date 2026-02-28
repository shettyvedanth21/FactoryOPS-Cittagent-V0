import json
import logging
from typing import Optional, Dict, Any
import httpx

from src.config import settings


logger = logging.getLogger(__name__)


class RedisClient:
    """Simple Redis client for caching."""
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        if key in self._cache:
            value, expiry = self._cache[key]
            import time
            if time.time() < expiry:
                return value
            else:
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: str, ex: int = 300):
        """Set value in cache with TTL."""
        import time
        self._cache[key] = (value, time.time() + ex)
    
    async def delete(self, key: str):
        """Delete key from cache."""
        if key in self._cache:
            del self._cache[key]


redis_cache = RedisClient()


async def enrich_device_metadata(device_id: str) -> Optional[Dict[str, Any]]:
    """
    Enrich device metadata from device-service.
    
    Uses Redis cache with TTL=300s (per LLD §16.2).
    
    Returns:
        Dict with device_name, device_type, location, tenant_id or None
    """
    cache_key = f"device:{device_id}:meta"
    
    cached = await redis_cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit for device {device_id}")
        return json.loads(cached)
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{settings.DEVICE_SERVICE_URL}/api/v1/devices/{device_id}"
            )
            
            if response.status_code == 404:
                logger.warning(f"Device {device_id} not found")
                return None
            
            if response.status_code != 200:
                logger.warning(f"Failed to get device {device_id}: {response.status_code}")
                return None
            
            data = response.json()
            if not data.get("success"):
                return None
            
            device_data = data.get("data", {})
            
            metadata = {
                "device_name": device_data.get("device_name"),
                "device_type": device_data.get("device_type"),
                "location": device_data.get("location"),
                "tenant_id": device_data.get("tenant_id")
            }
            
            await redis_cache.set(cache_key, json.dumps(metadata), ex=300)
            logger.info(f"Cached metadata for device {device_id}")
            
            return metadata
    
    except Exception as e:
        logger.error(f"Failed to enrich device {device_id}: {str(e)}")
        return None
