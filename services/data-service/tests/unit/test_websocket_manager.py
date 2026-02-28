import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestWebSocketManager:
    """Test WebSocket manager functionality."""
    
    @pytest.mark.asyncio
    async def test_connect_adds_websocket(self):
        """connect() should add websocket to registry."""
        from src.services.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        mock_ws = AsyncMock()
        
        await manager.connect("TEST-001", mock_ws)
        
        assert manager.get_connection_count("TEST-001") == 1
        mock_ws.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_disconnect_removes_websocket(self):
        """disconnect() should remove websocket from registry."""
        from src.services.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        mock_ws = AsyncMock()
        
        await manager.connect("TEST-001", mock_ws)
        await manager.disconnect("TEST-001", mock_ws)
        
        assert manager.get_connection_count("TEST-001") == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all_clients(self):
        """broadcast() should send to all connected clients."""
        from src.services.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        mock_ws1 = AsyncMock()
        mock_ws2 = AsyncMock()
        
        await manager.connect("TEST-001", mock_ws1)
        await manager.connect("TEST-001", mock_ws2)
        
        await manager.broadcast("TEST-001", {"test": "data"})
        
        mock_ws1.send_json.assert_called_once()
        mock_ws2.send_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_removes_dead_connections(self):
        """broadcast() should remove dead connections gracefully."""
        from src.services.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        mock_ws = AsyncMock()
        mock_ws.send_json.side_effect = Exception("Connection closed")
        
        await manager.connect("TEST-001", mock_ws)
        await manager.broadcast("TEST-001", {"test": "data"})
        
        assert manager.get_connection_count("TEST-001") == 0
    
    def test_get_connection_count(self):
        """get_connection_count() should return correct count."""
        from src.services.websocket_manager import WebSocketManager
        
        manager = WebSocketManager()
        
        assert manager.get_connection_count("TEST-001") == 0
