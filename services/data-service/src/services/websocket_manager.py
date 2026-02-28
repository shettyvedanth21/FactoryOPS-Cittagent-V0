import json
import logging
from typing import Dict, Set
from fastapi import WebSocket

from src.config import settings


logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time telemetry."""
    
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, device_id: str, websocket: WebSocket):
        """Register a WebSocket connection for a device."""
        await websocket.accept()
        
        if device_id not in self._connections:
            self._connections[device_id] = set()
        
        self._connections[device_id].add(websocket)
        logger.info(f"WebSocket connected for device {device_id}. Total: {len(self._connections[device_id])}")
    
    async def disconnect(self, device_id: str, websocket: WebSocket):
        """Unregister a WebSocket connection."""
        if device_id in self._connections:
            self._connections[device_id].discard(websocket)
            
            if not self._connections[device_id]:
                del self._connections[device_id]
            
            logger.info(f"WebSocket disconnected for device {device_id}")
    
    async def broadcast(self, device_id: str, data: dict):
        """Broadcast data to all connected clients for a device."""
        if device_id not in self._connections:
            return
        
        dead_connections = set()
        
        for websocket in self._connections[device_id]:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket for {device_id}: {str(e)}")
                dead_connections.add(websocket)
        
        for dead in dead_connections:
            await self.disconnect(device_id, dead)
    
    def get_connection_count(self, device_id: str) -> int:
        """Get the number of active connections for a device."""
        return len(self._connections.get(device_id, set()))
    
    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self._connections.values())


websocket_manager = WebSocketManager()
