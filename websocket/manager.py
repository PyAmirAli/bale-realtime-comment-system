from fastapi import WebSocket
from collections import defaultdict


class ConnectionManager:

    def __init__(self):
        self.rooms = defaultdict(list)

    async def connect(self, post_id: str, websocket: WebSocket):
        await websocket.accept()
        self.rooms[post_id].append(websocket)

    def disconnect(self, post_id: str, websocket: WebSocket):

        if websocket in self.rooms[post_id]:
            self.rooms[post_id].remove(websocket)

        if not self.rooms[post_id]:
            del self.rooms[post_id]

    async def broadcast(self, post_id: str, payload: dict):

        for ws in self.rooms.get(post_id, []):
            await ws.send_json(payload)


manager = ConnectionManager()
