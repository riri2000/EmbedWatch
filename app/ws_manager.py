"""Tracks connected dashboard WebSocket clients and broadcasts new
readings to all of them as they arrive."""
import logging

from fastapi import WebSocket

logger = logging.getLogger("embedwatch.ws")


class ConnectionManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info("dashboard client connected (%d total)", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info("dashboard client disconnected (%d total)", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        stale = []
        for ws in self._connections:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)
