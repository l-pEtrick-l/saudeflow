"""Tempo real: WebSocket + barramento de eventos com fallback por polling.

O frontend tenta WebSocket e, se falhar, faz polling dos endpoints REST.
"""

import asyncio
import json
from typing import Dict, List, Optional, Set

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.channels: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channels: List[str]) -> None:
        await websocket.accept()
        for channel in channels:
            self.channels.setdefault(channel, set()).add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        for channel in list(self.channels.keys()):
            self.channels[channel].discard(websocket)
            if not self.channels[channel]:
                self.channels.pop(channel, None)

    async def broadcast(self, channel: str, payload: dict) -> None:
        dead = []
        for websocket in list(self.channels.get(channel, [])):
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)


manager = ConnectionManager()


class EventBus:
    """Desacopla serviços (síncronos) do loop asyncio do WebSocket."""

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: Optional[asyncio.Queue] = None
        self._pending: List[dict] = []

    def bind(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop
        self._queue = asyncio.Queue()
        for item in self._pending:
            self._queue.put_nowait(item)
        self._pending = []

    def publish(self, channel: str, payload: dict) -> None:
        item = {"channel": channel, "payload": payload}
        if self._loop and self._queue:
            try:
                self._loop.call_soon_threadsafe(self._queue.put_nowait, item)
                return
            except RuntimeError:
                pass
        self._pending.append(item)

    async def consume(self) -> None:
        if not self._queue:
            return
        while True:
            item = await self._queue.get()
            await manager.broadcast(item["channel"], item["payload"])


bus = EventBus()


def publish_event(channel: str, payload: dict) -> None:
    bus.publish(channel, payload)


def channel_for_request(request_id: str) -> str:
    return f"request:{request_id}"


def channel_for_unit(unit_id: str) -> str:
    return f"unit:{unit_id}"


def channel_for_alert(alert_id: str) -> str:
    return f"alert:{alert_id}"


def channel_for_user(user_id: str) -> str:
    return f"user:{user_id}"


def event_message(event_type: str, data: dict) -> dict:
    return {"type": event_type, "data": data}
