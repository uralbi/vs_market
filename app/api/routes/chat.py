from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.services.chat_service import ChatService

router = APIRouter(
    prefix='/chat',
    tags=['Chat']
)


@router.get("/{user1_id}/{user2_id}")
def get_chat_history(user1_id: int, user2_id: int, db: Session = Depends(get_db)):
    chat_service = ChatService(db)
    messages = chat_service.get_chat_history(user1_id, user2_id)

    return {
        "messages": [
            {"sender_id": msg.sender_id, "content": msg.content, "timestamp": msg.timestamp}
            for msg in messages
        ]
    }
