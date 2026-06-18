import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.redis_client import get_redis_client
from app.services.checker import live_status_store
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    await websocket.accept()
    
    # Send current state immediately on connection
    live_state = await live_status_store.get_all()
    await websocket.send_json(live_state)
    
    redis = await get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.subscribe("monitor-status")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                event = json.loads(message["data"])
                await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await pubsub.unsubscribe("monitor-status")
        await pubsub.close()
