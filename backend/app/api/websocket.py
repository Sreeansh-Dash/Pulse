import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        text_data = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(text_data)
            except Exception as e:
                logger.error(f"Error sending to websocket: {e}")
                self.disconnect(connection)

manager = ConnectionManager()
router = APIRouter()

@router.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send current state immediately on connection
        from app.services.checker import live_status_store
        live_state = await live_status_store.get_all()
        await websocket.send_json(live_state)
        
        while True:
            # We don't expect messages from the client, just keep the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
