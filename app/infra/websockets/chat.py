from fastapi import WebSocket
from typing import Dict

active_connections: Dict[int, WebSocket] = {}

async def connect(user_id: int, websocket: WebSocket):
    await websocket.accept()
    active_connections[user_id] = websocket

async def disconnect(user_id: int):
    active_connections.pop(user_id, None)
