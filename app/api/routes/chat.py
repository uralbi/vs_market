from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.services.chat_service import ChatService
from app.domain.security.auth_user import user_authorization
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
    prefix='/chat',
    tags=['Chat']
)

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.get("/messages")
def get_chat_history(user2_id: int, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Fetch chat history between the authenticated user and another user.
    """
    user = user_authorization(token, db)
    chat_service = ChatService(db)
    messages = chat_service.get_chat_history(user.id, user2_id)

    return {
        "messages": [
            {"sender_id": msg.sender_id, "content": msg.content, "timestamp": msg.timestamp}
            for msg in messages
        ]
    }

@router.get("/rooms")
def get_user_chat_rooms(token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Fetch all chat rooms for the authenticated user.
    """
    user = user_authorization(token, db)
    chat_service = ChatService(db)
    chat_rooms = chat_service.get_user_chat_rooms(user.id)

    return [
        {
            "chat_room_id": room.id,
            "other_user_id": room.user2_id if room.user1_id == user.id else room.user1_id,
        }
        for room in chat_rooms
    ]