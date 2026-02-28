import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.config import settings
from src.influx.client import influx_client
from src.services.enrichment import enrich_device_metadata
from src.services.rule_trigger import trigger_rule_evaluation
from src.services.websocket_manager import websocket_manager
from src.services.properties import discover_device_properties


logger = logging.getLogger(__name__)


class DeadLetterQueue:
    """Simple in-memory DLQ for failed messages."""
    
    def __init__(self, max_size: int = 1000):
        self._queue: List[Dict[str, Any]] = []
        self._max_size = max_size
    
    def add(self, message: Dict[str, Any]):
        """Add a message to the DLQ."""
        self._queue.append({
            **message,
            "queued_at": datetime.utcnow().isoformat()
        })
        
        if len(self._queue) > self._max_size:
            self._queue.pop(0)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all messages in DLQ."""
        return self._queue.copy()
    
    def clear(self):
        """Clear the DLQ."""
        self._queue.clear()


dlq = DeadLetterQueue()


class TelemetryHandler:
    """Handler for processing telemetry messages through the pipeline."""
    
    async def handle_telemetry(self, device_id: str, payload: str):
        """
        Process telemetry message through the pipeline.
        
        Pipeline steps:
        1. Parse JSON payload
        2. Validate structure
        3. Enrich device metadata
        4. Write to InfluxDB
        5. Trigger rule evaluation
        6. Update device heartbeat
        7. Broadcast via WebSocket
        8. Auto-discover properties
        """
        logger.info(f"Processing telemetry for device: {device_id}")
        
        enrichment_status = "success"
        
        step = "parse_json"
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            logger.error(f"Step {step}: JSON parse error for {device_id}: {str(e)}")
            dlq.add({
                "device_id": device_id,
                "payload": payload,
                "error": f"JSON parse error: {str(e)}",
                "step": step
            })
            return
        
        step = "validate_structure"
        if not isinstance(data, dict) or "data" not in data:
            logger.error(f"Step {step}: Invalid structure for {device_id}")
            dlq.add({
                "device_id": device_id,
                "payload": payload,
                "error": "Missing 'data' field",
                "step": step
            })
            return
        
        telemetry_data = data.get("data", {})
        timestamp_str = data.get("timestamp")
        
        try:
            timestamp = (
                datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if timestamp_str
                else datetime.utcnow()
            )
        except ValueError:
            timestamp = datetime.utcnow()
        
        step = "enrich"
        metadata = await enrich_device_metadata(device_id)
        if metadata is None:
            enrichment_status = "failed"
            logger.warning(f"Step {step}: Enrichment failed for {device_id}")
        
        step = "write_influxdb"
        write_success = influx_client.write_telemetry(
            device_id=device_id,
            fields=telemetry_data,
            timestamp=timestamp,
            enrichment_status=enrichment_status
        )
        
        if not write_success:
            logger.error(f"Step {step}: InfluxDB write failed for {device_id}")
            dlq.add({
                "device_id": device_id,
                "payload": payload,
                "error": "InfluxDB write failed",
                "step": step
            })
        
        step = "trigger_rules"
        try:
            await trigger_rule_evaluation(device_id, telemetry_data)
        except Exception as e:
            logger.warning(f"Step {step}: Rule trigger failed for {device_id}: {str(e)}")
        
        step = "update_heartbeat"
        try:
            await self._update_heartbeat(device_id)
        except Exception as e:
            logger.warning(f"Step {step}: Heartbeat update failed for {device_id}: {str(e)}")
        
        step = "broadcast_websocket"
        try:
            await self._broadcast_websocket(device_id, telemetry_data, timestamp)
        except Exception as e:
            logger.warning(f"Step {step}: WebSocket broadcast failed for {device_id}: {str(e)}")
        
        step = "discover_properties"
        try:
            await discover_device_properties(device_id, telemetry_data)
        except Exception as e:
            logger.warning(f"Step {step}: Property discovery failed for {device_id}: {str(e)}")
        
        logger.info(f"Completed telemetry processing for device: {device_id}")
    
    async def _update_heartbeat(self, device_id: str):
        """Update device last_seen_timestamp via HTTP."""
        import httpx
        
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    f"{settings.DEVICE_SERVICE_URL}/api/v1/devices/{device_id}/heartbeat"
                )
        except Exception as e:
            logger.warning(f"Heartbeat update failed for {device_id}: {str(e)}")
    
    async def _broadcast_websocket(self, device_id: str, data: Dict[str, Any], timestamp: datetime):
        """Broadcast telemetry to WebSocket clients."""
        message = {
            "device_id": device_id,
            "timestamp": timestamp.isoformat(),
            "data": data
        }
        await websocket_manager.broadcast(device_id, message)


telemetry_handler = TelemetryHandler()
