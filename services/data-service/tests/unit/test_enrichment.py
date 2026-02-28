import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestEnrichment:
    """Test enrichment service functionality."""
    
    @pytest.mark.asyncio
    @patch("src.services.enrichment.httpx.AsyncClient")
    async def test_successful_enrichment(self, mock_client_class):
        """Successful enrichment should return device metadata."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "device_id": "COMPRESSOR-001",
                "device_name": "Test Compressor",
                "device_type": "compressor",
                "location": "Building A",
                "tenant_id": "tenant-1"
            }
        }
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        from src.services.enrichment import enrich_device_metadata
        
        result = await enrich_device_metadata("COMPRESSOR-001")
        
        assert result is not None
        assert result["device_name"] == "Test Compressor"
        assert result["device_type"] == "compressor"
    
    @pytest.mark.asyncio
    @patch("src.services.enrichment.httpx.AsyncClient")
    async def test_404_returns_none(self, mock_client_class):
        """404 from device-service should return None."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        from src.services.enrichment import enrich_device_metadata
        
        result = await enrich_device_metadata("NONEXISTENT")
        
        assert result is None
    
    @pytest.mark.asyncio
    @patch("src.services.enrichment.redis_cache")
    async def test_cache_hit(self, mock_cache):
        """Cache hit on second call should return cached data."""
        import json
        
        mock_cache.get.return_value = json.dumps({
            "device_name": "Cached Device",
            "device_type": "compressor"
        })
        
        from src.services.enrichment import enrich_device_metadata
        
        result = await enrich_device_metadata("COMPRESSOR-001")
        
        assert result is not None
        assert result["device_name"] == "Cached Device"


class TestRuleTrigger:
    """Test rule trigger service functionality."""
    
    @pytest.mark.asyncio
    @patch("src.services.rule_trigger.httpx.AsyncClient")
    async def test_trigger_successful(self, mock_client_class):
        """Successful trigger should call rule engine."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        from src.services.rule_trigger import trigger_rule_evaluation
        
        await trigger_rule_evaluation("COMPRESSOR-001", {"power": 100})
        
        mock_client.post.assert_called_once()
    
    @pytest.mark.asyncio
    @patch("src.services.rule_trigger.httpx.AsyncClient")
    async def test_trigger_timeout_non_blocking(self, mock_client_class):
        """Timeout should not raise exception."""
        import httpx
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.side_effect = httpx.TimeoutException()
        mock_client_class.return_value = mock_client
        
        from src.services.rule_trigger import trigger_rule_evaluation
        
        await trigger_rule_evaluation("COMPRESSOR-001", {"power": 100})


class TestProperties:
    """Test property discovery functionality."""
    
    @pytest.mark.asyncio
    @patch("src.services.properties.httpx.AsyncClient")
    async def test_discover_numeric_property(self, mock_client_class):
        """Numeric properties should be discovered."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        from src.services.properties import discover_device_properties
        
        await discover_device_properties("COMPRESSOR-001", {"power": 100, "temperature": 50})
        
        assert mock_client.post.call_count >= 1
