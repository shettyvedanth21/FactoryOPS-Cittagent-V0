from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.services.websocket_manager import websocket_manager


router = APIRouter()


@router.websocket("/ws/telemetry/{device_id}")
async def websocket_telemetry(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for real-time telemetry streaming."""
    await websocket_manager.connect(device_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket_manager.disconnect(device_id, websocket)
    except Exception as e:
        await websocket_manager.disconnect(device_id, websocket)
