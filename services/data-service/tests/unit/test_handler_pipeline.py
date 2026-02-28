import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestHandlerPipeline:
    """Test telemetry message handler pipeline."""
    
    @pytest.mark.asyncio
    async def test_valid_telemetry_flows_through_pipeline(self):
        """Valid telemetry should flow through all steps."""
        payload = '{"timestamp": "2026-02-27T10:00:01Z", "data": {"power": 100}}'
        
        with patch("src.mqtt.handler.influx_client") as mock_influx, \
             patch("src.mqtt.handler.enrich_device_metadata") as mock_enrich, \
             patch("src.mqtt.handler.trigger_rule_evaluation") as mock_trigger, \
             patch("src.mqtt.handler.websocket_manager") as mock_ws, \
             patch("src.mqtt.handler.discover_device_properties") as mock_props:
            
            mock_influx.write_telemetry.return_value = True
            mock_enrich.return_value = {"device_name": "Test"}
            mock_trigger.return_value = AsyncMock()
            mock_ws.broadcast.return_value = AsyncMock()
            mock_props.return_value = AsyncMock()
            
            from src.mqtt.handler import telemetry_handler
            
            await telemetry_handler.handle_telemetry("COMPRESSOR-001", payload)
            
            mock_influx.write_telemetry.assert_called_once()
            mock_trigger.assert_called_once()
            mock_ws.broadcast.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalid_json_sends_to_dlq(self):
        """Invalid JSON should be sent to DLQ."""
        payload = "not valid json"
        
        with patch("src.mqtt.handler.dlq") as mock_dlq:
            from src.mqtt.handler import telemetry_handler
            
            await telemetry_handler.handle_telemetry("COMPRESSOR-001", payload)
            
            mock_dlq.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_missing_data_field_sends_to_dlq(self):
        """Missing 'data' field should be sent to DLQ."""
        payload = '{"timestamp": "2026-02-27T10:00:01Z"}'
        
        with patch("src.mqtt.handler.dlq") as mock_dlq:
            from src.mqtt.handler import telemetry_handler
            
            await telemetry_handler.handle_telemetry("COMPRESSOR-001", payload)
            
            mock_dlq.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enrichment_failure_continues_pipeline(self):
        """Enrichment failure should continue pipeline with enrichment_status=failed."""
        payload = '{"data": {"power": 100}}'
        
        with patch("src.mflux.handler.influx_client") as mock_influx, \
             patch("src.mqtt.handler.enrich_device_metadata") as mock_enrich:
            
            mock_enrich.return_value = None
            mock_influx.write_telemetry.return_value = True
            
            from src.mqtt.handler import telemetry_handler
            
            await telemetry_handler.handle_telemetry("COMPRESSOR-001", payload)
            
            mock_influx.write_telemetry.assert_called_once()
            call_args = mock_influx.write_telemetry.call_args
            assert call_args.kwargs.get("enrichment_status") == "failed"
    
    @pytest.mark.asyncio
    async def test_influxdb_failure_sends_to_dlq(self):
        """InfluxDB write failure should send to DLQ."""
        payload = '{"data": {"power": 100}}'
        
        with patch("src.mqtt.handler.influx_client") as mock_influx, \
             patch("src.mqtt.handler.enrich_device_metadata") as mock_enrich, \
             patch("src.mqtt.handler.dlq") as mock_dlq:
            
            mock_enrich.return_value = {"device_name": "Test"}
            mock_influx.write_telemetry.return_value = False
            
            from src.mqtt.handler import telemetry_handler
            
            await telemetry_handler.handle_telemetry("COMPRESSOR-001", payload)
            
            mock_dlq.add.assert_called()
    
    @pytest.mark.asyncio
    async def test_rule_trigger_failure_non_blocking(self):
        """Rule trigger failure should not affect pipeline."""
        payload = '{"data": {"power": 100}}'
        
        with patch("src.mqtt.handler.influx_client") as mock_influx, \
             patch("src.mqtt.handler.enrich_device_metadata") as mock_enrich, \
             patch("src.mqtt.handler.trigger_rule_evaluation") as mock_trigger:
            
            mock_enrich.return_value = {"device_name": "Test"}
            mock_influx.write_telemetry.return_value = True
            mock_trigger.side_effect = Exception("Rule engine down")
            
            from src.mqtt.handler import telemetry_handler
            
            await telemetry_handler.handle_telemetry("COMPRESSOR-001", payload)
            
            mock_influx.write_telemetry.assert_called_once()
