from fastapi import APIRouter
from .websocket import router as websocket_router
from .routes import router as rest_router

router = APIRouter()
router.include_router(websocket_router)
router.include_router(rest_router)
