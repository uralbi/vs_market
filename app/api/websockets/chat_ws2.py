from fastapi import APIRouter, WebSocket, Depends
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.api.websockets.ws_consumer import ChatConsumer
from app.domain.security.auth_user import user_authorization

router = APIRouter(
    prefix='/ws/v2/chat',
    tags=['Chat Websocket']
)

chat_consumer = ChatConsumer()

@router.websocket("/{receiverid}/{subject}")
async def websocket_chat(websocket: WebSocket, receiverid: str, subject: str, db: Session = Depends(get_db)):
    """WebSocket route that delegates connection handling to ChatConsumer."""
    if not receiverid:
        print('not receiver id')
        return
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return
    user = user_authorization(token, db)
    user_id = user.id
    
    if user_id == receiverid:
        await websocket.close(code=1003, reason="No counterpart")
        return
    await chat_consumer.connect(websocket, user, receiverid, db)
    await chat_consumer.receive_message(websocket, user.id, subject, db)
