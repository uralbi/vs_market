from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.infra.websockets.ws_consumer import ChatConsumer

router = APIRouter(
    prefix='/ws/v2/chat',
    tags=['Chat Websocket']
)

chat_consumer = ChatConsumer()

@router.websocket("/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: int, db: Session = Depends(get_db)):
    """WebSocket route that delegates connection handling to ChatConsumer."""
    await chat_consumer.connect(websocket, user_id, db)
    await chat_consumer.receive_message(websocket, user_id)
