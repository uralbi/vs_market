from fastapi import WebSocket
from app.infra.websockets.chat import connect, disconnect

async def websocket_endpoint(user_id: int, websocket: WebSocket):
    await connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Process chat messages here
    except Exception:
        await disconnect(user_id)

