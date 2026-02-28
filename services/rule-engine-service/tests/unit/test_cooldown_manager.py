import pytest
from unittest.mock import AsyncMock, patch

from app.services.cooldown_manager import CooldownManager


class TestCooldownManager:
    @pytest.fixture
    def cooldown_manager(self):
        return CooldownManager()
    
    @pytest.mark.asyncio
    async def test_is_cooling_down_returns_false_for_new_rule_device(self, cooldown_manager):
        with patch.object(cooldown_manager, 'get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.exists.return_value = 0
            mock_get_redis.return_value = mock_redis
            
            result = await cooldown_manager.is_cooling_down("rule-1", "COMPRESSOR-001")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_set_cooldown_then_is_cooling_down_returns_true(self, cooldown_manager):
        with patch.object(cooldown_manager, 'get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.setex.return_value = True
            mock_redis.exists.return_value = 1
            mock_get_redis.return_value = mock_redis
            
            await cooldown_manager.set_cooldown("rule-1", "COMPRESSOR-001", 15)
            result = await cooldown_manager.is_cooling_down("rule-1", "COMPRESSOR-001")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_clear_cooldown(self, cooldown_manager):
        with patch.object(cooldown_manager, 'get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.delete.return_value = 1
            mock_get_redis.return_value = mock_redis
            
            await cooldown_manager.clear_cooldown("rule-1", "COMPRESSOR-001")
            mock_redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ttl_is_set_correctly(self, cooldown_manager):
        with patch.object(cooldown_manager, 'get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.setex.return_value = True
            mock_get_redis.return_value = mock_redis
            
            await cooldown_manager.set_cooldown("rule-1", "COMPRESSOR-001", 15)
            mock_redis.setex.assert_called_once_with(
                "cooldown:rule-1:COMPRESSOR-001",
                900,
                '{"rule_id": "rule-1", "device_id": "COMPRESSOR-001"}'
            )
