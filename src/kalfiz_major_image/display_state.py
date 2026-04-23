from __future__ import annotations

import asyncio
import json
from collections.abc import Iterable

from fastapi import WebSocket

from .models import DisplayState, DisplayStateUpdate


class DisplayStateStore:
    def __init__(self, initial_state: DisplayState | None = None) -> None:
        self._state = initial_state or DisplayState()
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    def snapshot(self) -> DisplayState:
        return self._state.model_copy(deep=True)

    async def update(self, update: DisplayStateUpdate) -> DisplayState:
        async with self._lock:
            changed = self._state.model_dump()
            incoming = update.model_dump(exclude_unset=True)
            if "grid" in incoming and incoming["grid"] is not None:
                changed["grid"] = incoming["grid"]
            for key, value in incoming.items():
                if key == "grid":
                    continue
                changed[key] = value
            self._state = DisplayState(**changed)
        await self.broadcast()
        return self.snapshot()

    async def apply_selection(self, media_path: str) -> DisplayState:
        return await self.update(
            DisplayStateUpdate(
                active_media_path=media_path,
                pending_media_path=media_path,
                applied=True,
            )
        )

    async def register(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)
        await websocket.send_text(self.snapshot_json())

    def unregister(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    def snapshot_json(self) -> str:
        return json.dumps(self.snapshot().model_dump(mode="json"))

    async def broadcast(self) -> None:
        if not self._connections:
            return
        payload = self.snapshot_json()
        stale: list[WebSocket] = []
        for websocket in self._connections:
            try:
                await websocket.send_text(payload)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.unregister(websocket)

    async def close_all(self) -> None:
        connections: Iterable[WebSocket] = tuple(self._connections)
        for websocket in connections:
            try:
                await websocket.close()
            finally:
                self.unregister(websocket)
