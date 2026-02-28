import redis.asyncio as redis
from typing import Optional, Any
import json

from app.config import settings


class RedisClient:
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def connect(self):
        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
    
    async def disconnect(self):
        if self._client:
            await self._client.close()
    
    async def get(self, key: str) -> Optional[str]:
        if not self._client:
            return None
        return await self._client.get(key)
    
    async def set(self, key: str, value: Any, ex: int = None) -> bool:
        if not self._client:
            return False
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        return await self._client.set(key, value, ex=ex)
    
    async def delete(self, *keys: str) -> int:
        if not self._client:
            return 0
        return await self._client.delete(*keys)
    
    async def exists(self, key: str) -> bool:
        if not self._client:
            return False
        return await self._client.exists(key) > 0


redis_client = RedisClient()


async def get_redis() -> RedisClient:
    return redis_client
