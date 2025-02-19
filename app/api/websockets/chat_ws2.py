from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.api.websockets.ws_consumer import ChatConsumer

router = APIRouter(
    prefix='/ws/v2/chat',
    tags=['Chat Websocket']
)

chat_consumer = ChatConsumer()

@router.websocket("/{user_id}/{receiverid}")
async def websocket_chat(websocket: WebSocket, user_id: int, receiverid: int, db: Session = Depends(get_db)):
    """WebSocket route that delegates connection handling to ChatConsumer."""
    if user_id == receiverid:
        await websocket.close(code=1003, reason="No counterpart")
        return
    await chat_consumer.connect(websocket, user_id, receiverid, db)
    await chat_consumer.receive_message(websocket, user_id, receiverid, db)
