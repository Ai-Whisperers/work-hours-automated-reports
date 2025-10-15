"""WebSocket connection manager for real-time updates."""

import json
import logging
from typing import Dict, Set
from fastapi import WebSocket


logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasts."""

    def __init__(self):
        """Initialize WebSocket manager."""
        # Store active connections: {report_id: set of websockets}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store all connections
        self.all_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, report_id: str = None):
        """Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            report_id: Optional report ID to subscribe to
        """
        await websocket.accept()
        self.all_connections.add(websocket)

        if report_id:
            if report_id not in self.active_connections:
                self.active_connections[report_id] = set()
            self.active_connections[report_id].add(websocket)

        logger.info(f"WebSocket connected. Report ID: {report_id}, Total connections: {len(self.all_connections)}")

    def disconnect(self, websocket: WebSocket, report_id: str = None):
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            report_id: Optional report ID to unsubscribe from
        """
        self.all_connections.discard(websocket)

        if report_id and report_id in self.active_connections:
            self.active_connections[report_id].discard(websocket)
            if not self.active_connections[report_id]:
                del self.active_connections[report_id]

        logger.info(f"WebSocket disconnected. Report ID: {report_id}, Total connections: {len(self.all_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection.

        Args:
            message: Message dictionary
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.all_connections.discard(websocket)

    async def broadcast_to_report(self, report_id: str, message: dict):
        """Broadcast a message to all connections subscribed to a report.

        Args:
            report_id: Report ID
            message: Message dictionary
        """
        if report_id not in self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections[report_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection, report_id)

    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all active connections.

        Args:
            message: Message dictionary
        """
        disconnected = set()

        for connection in self.all_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.all_connections.discard(connection)

    async def send_progress_update(self, report_id: str, progress: float, message: str):
        """Send a progress update for a report.

        Args:
            report_id: Report ID
            progress: Progress value (0.0 to 1.0)
            message: Progress message
        """
        await self.broadcast_to_report(
            report_id,
            {
                "type": "progress",
                "report_id": report_id,
                "progress": progress,
                "message": message
            }
        )

    async def send_status_update(self, report_id: str, status: str, message: str = None, error: str = None):
        """Send a status update for a report.

        Args:
            report_id: Report ID
            status: Status string (pending, processing, completed, failed)
            message: Optional status message
            error: Optional error message
        """
        data = {
            "type": "status",
            "report_id": report_id,
            "status": status,
        }

        if message:
            data["message"] = message
        if error:
            data["error"] = error

        await self.broadcast_to_report(report_id, data)

    async def send_completion_update(self, report_id: str, download_url: str):
        """Send a completion notification with download URL.

        Args:
            report_id: Report ID
            download_url: URL to download the report
        """
        await self.broadcast_to_report(
            report_id,
            {
                "type": "completed",
                "report_id": report_id,
                "status": "completed",
                "download_url": download_url,
                "message": "Report generated successfully"
            }
        )


# Global WebSocket manager instance
ws_manager = WebSocketManager()
