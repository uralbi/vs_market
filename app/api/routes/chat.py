from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.services.chat_service import ChatService
from app.services.user_service import UserService
from app.domain.security.auth_user import user_authorization
from fastapi.security import OAuth2PasswordBearer

router = APIRouter(
        prefix='/api/chat',
        tags=['Chat']
    )

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.post("/create_room")
def create_chat_room(receiver_id: str = Query(..., description="ID of the user to chat with"), 
                     subject: str = Query(..., description="Subject of the chat"), 
                     token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """Create or get a chat room between the authenticated user and another user."""    
    user = user_authorization(token, db)
    if user.id == receiver_id:
        raise HTTPException(status_code=400, detail="Cannot create chat room with yourself")
    
    chat_service = ChatService(db)
    chat_room = chat_service.get_or_create_chat_room(user.id, receiver_id, subject)
    
    return {
        "chat_room_id": chat_room.id,
        # "user1_id": chat_room.user1_id,
        # "user2_id": chat_room.user2_id,
        # "subject": chat_room.subject
    }

@router.get("/counterpart")
def get_other_user(token: str = Depends(token_scheme), room_id: str = Query(..., description="chat room id"), db: Session = Depends(get_db)):
    """
    Fetch the other user (counterpart) in a given chat room.
    """
    user = user_authorization(token, db)
    chat_service = ChatService(db)
    other_user_id = chat_service.get_other_user_id(room_id, user.id)
    user_service = UserService(db)
    other_user = user_service.get_user_by_id(other_user_id)
    return {"other_user_id": other_user_id, "other_username": other_user.username}


@router.delete("/rooms/{chat_room_id}")
def delete_chat_room(chat_room_id: str, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
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
def get_chat_history(room_id: str, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """ß
    Fetch chat history between the authenticated user and another user.
    """
    user = user_authorization(token, db)
    chat_service = ChatService(db)
    messages = chat_service.get_chat_history(room_id, user.id)
    chat_service.mark_messages_as_read(user.id, [room_id,])
    room = chat_service.get_chat_room_by_id(room_id)
    return {
        "subject" : room.subject,
        "user_id" : user.id,
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
    
    return [
        {   
            "chat_room_id": room['chat_room_id'],  
            "other_user_id": room["other_user_id"],  
            "other_username": room["other_user_username"],
            "has_unread_messages": room["has_unread_messages"],
            "subject": room['subject'],
        }
        for room in chat_rooms
    ]
