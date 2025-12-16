"""WebSocket endpoints for real-time updates."""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..middleware import WebSocketManager


router = APIRouter()
logger = logging.getLogger(__name__)

# WebSocket manager instance
ws_manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """General WebSocket endpoint for all updates.

    Args:
        websocket: WebSocket connection
    """
    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            logger.debug(f"Received message: {data}")

            # Echo back for heartbeat
            await ws_manager.send_personal_message(
                {"type": "pong", "message": "Connection alive"}, websocket
            )

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket disconnected")


@router.websocket("/ws/report/{report_id}")
async def report_websocket_endpoint(websocket: WebSocket, report_id: str):
    """WebSocket endpoint for specific report updates.

    Args:
        websocket: WebSocket connection
        report_id: Report ID to subscribe to
    """
    await ws_manager.connect(websocket, report_id)

    try:
        # Send initial connection confirmation
        await ws_manager.send_personal_message(
            {
                "type": "connected",
                "report_id": report_id,
                "message": f"Subscribed to report {report_id}",
            },
            websocket,
        )

        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            logger.debug(f"Received message for report {report_id}: {data}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, report_id)
        logger.info(f"WebSocket disconnected from report {report_id}")
