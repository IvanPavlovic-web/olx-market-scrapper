import asyncio
import uuid
from collections import defaultdict
from typing import Any
from fastapi import WebSocket
from app.core.logging import log


class WSManager:
    def __init__(self) -> None:
        self._sockets: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._sockets[user_id].add(ws)
        log.info("ws_connected", user=str(user_id), total=len(self._sockets[user_id]))

    async def disconnect(self, user_id: uuid.UUID, ws: WebSocket) -> None:
        async with self._lock:
            self._sockets[user_id].discard(ws)
            if not self._sockets[user_id]:
                self._sockets.pop(user_id, None)

    async def send_user(self, user_id: uuid.UUID, message: dict[str, Any]) -> None:
        sockets = list(self._sockets.get(user_id, set()))
        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception:
                await self.disconnect(user_id, ws)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for user_id in list(self._sockets.keys()):
            await self.send_user(user_id, message)


ws_manager = WSManager()
