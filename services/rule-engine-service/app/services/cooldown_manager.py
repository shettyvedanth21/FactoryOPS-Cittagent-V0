import json
from typing import Optional

import redis.asyncio as redis

from app.config import settings


class CooldownManager:
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
    
    async def get_redis(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True
            )
        return self._redis
    
    def _get_key(self, rule_id: str, device_id: str) -> str:
        return f"cooldown:{rule_id}:{device_id}"
    
    async def is_cooling_down(self, rule_id: str, device_id: str) -> bool:
        key = self._get_key(rule_id, device_id)
        redis_client = await self.get_redis()
        exists = await redis_client.exists(key)
        return exists > 0
    
    async def set_cooldown(self, rule_id: str, device_id: str, minutes: int) -> None:
        key = self._get_key(rule_id, device_id)
        redis_client = await self.get_redis()
        ttl_seconds = minutes * 60
        await redis_client.setex(key, ttl_seconds, json.dumps({"rule_id": rule_id, "device_id": device_id}))
    
    async def clear_cooldown(self, rule_id: str, device_id: str) -> None:
        key = self._get_key(rule_id, device_id)
        redis_client = await self.get_redis()
        await redis_client.delete(key)
    
    async def close(self):
        if self._redis:
            await self._redis.close()


cooldown_manager = CooldownManager()
