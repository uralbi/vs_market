from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.services.chat_service import ChatService
from app.services.user_service import UserService
from app.domain.security.auth_user import user_authorization
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
        prefix='/chat',
        tags=['Chat']
    )

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.delete("/rooms/{chat_room_id}")
def delete_chat_room(chat_room_id: int, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Delete a chat room and all associated messages.
    """
    user = user_authorization(token, db)
    chat_service = ChatService(db)    
    chat_room = chat_service.get_chat_room_by_id(chat_room_id)
    
    if not chat_room:
        raise HTTPException(status_code=404, detail="Chat room not found")

    if user.id not in [chat_room.user1_id, chat_room.user2_id]:
        raise HTTPException(status_code=403, detail="You are not allowed to delete this chat room")

    chat_service.delete_chat_room(chat_room)

    return {"message": "Chat room deleted successfully"}


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
            {
                "sender_id": sender_id,
                "sender_username": sender_username,  # Add sender's username
                "content": content,
                "timestamp": timestamp
            }
            for sender_id, sender_username, content, timestamp in messages  # Unpack query results
        ]
    }


@router.get("/rooms")
def get_user_chat_rooms(token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Fetch all chat rooms for the authenticated user, including unread message status.
    """
    user = user_authorization(token, db)
    chat_service = ChatService(db)
    chat_rooms = chat_service.get_user_chat_rooms(user.id)

    for r in chat_rooms:
        print(r.items())
    return [
        {
            "chat_room_id": room['chat_room_id'],  
            "other_user_id": room["other_user_id"],  
            "other_username": room["other_user_username"],
            "has_unread_messages": room["has_unread_messages"] 
        }
        for room in chat_rooms
    ]
