from collections import defaultdict
from datetime import datetime, timezone

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._rooms: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, trip_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms[trip_id].add(ws)

    def disconnect(self, trip_id: int, ws: WebSocket) -> None:
        self._rooms[trip_id].discard(ws)

    async def broadcast(self, trip_id: int, payload: dict) -> None:
        dead = set()
        for ws in list(self._rooms[trip_id]):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.add(ws)
        self._rooms[trip_id] -= dead

    async def broadcast_system(
        self, trip_id: int, content: str
    ) -> None:
        await self.broadcast(
            trip_id,
            {
                "type": "system",
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )


manager = ConnectionManager()
