"""
XVault WebSocket Endpoint & Broadcast System

All connected frontend clients receive real-time events:
- agent_status_update: agent status changes
- agent_decision: agent decisions with reasoning
- agent_message: agent-to-agent communications
- transaction_update: trade confirmations
- treasury_update: portfolio value changes
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

log = structlog.get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections and message broadcasting."""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        log.info("ws.client_connected", total=len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.remove(ws)
        log.info("ws.client_disconnected", total=len(self._connections))

    async def broadcast(self, event: str, data: Any) -> None:
        """Send an event to all connected clients."""
        if not self._connections:
            return

        message = json.dumps({
            "event": event,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)

        for ws in dead:
            self._connections.remove(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


# Singleton manager
manager = ConnectionManager()


async def broadcast(event: str, data: Any) -> None:
    """Module-level broadcast helper — imported by agents."""
    await manager.broadcast(event, data)


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        # Send initial connection confirmation
        await ws.send_text(json.dumps({
            "event": "connected",
            "data": {"message": "XVault WebSocket connected"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }))

        # Keep connection alive, handle ping/pong
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)

            if msg.get("type") == "ping":
                await ws.send_text(json.dumps({
                    "event": "pong",
                    "data": {},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }))

    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception as e:
        log.error("ws.error", error=str(e))
        manager.disconnect(ws)
