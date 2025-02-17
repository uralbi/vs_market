from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.services.chat_service import ChatService
from typing import Dict
from datetime import datetime

router = APIRouter(
    prefix='/ws/chat',
    tags=['Chat Websocket']
)

active_connections: Dict[int, WebSocket] = {}  # Stores user connections


@router.websocket("/{user_id}/{receiverid}")
async def websocket_chat(websocket: WebSocket, user_id: int, receiverid: int, db: Session = Depends(get_db)):
    await websocket.accept()
    active_connections[f"{user_id}-{receiverid}"] = websocket
    chat_service = ChatService(db)

    try:
        while True:
            data = await websocket.receive_json()
            receiver_id = data["receiver_id"]
            message_content = data["message"]

            chat_room = chat_service.get_or_create_chat_room(user_id, receiver_id)
            chat_service.save_message(chat_room.id, user_id, message_content)

            if receiver_id in active_connections:
                await active_connections[receiver_id].send_json({
                    "sender_id": user_id,
                    "message": message_content,
                    "timestamp": str(datetime.utcnow())
                })

    except WebSocketDisconnect:
        del active_connections[f"{user_id}-{receiverid}"]
