from fastapi import HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.infra.repositories.chat_repository import ChatRepository


class ChatService:
    def __init__(self, db: Session):
        self.repo = ChatRepository(db)

    def get_or_create_chat_room(self, user1_id: int, user2_id: int, subject: str):
        if user1_id == user2_id:
            raise HTTPException(status_code=403, detail="No counterport")
        return self.repo.get_or_create_chat_room(user1_id, user2_id, subject)

    def get_unread_chat_rooms(self, user_id: int):
        return self.repo.get_unread_chat_rooms(user_id)
    
    def save_message(self, chat_room_id: int, sender_id: int, content: str):
        return self.repo.save_message(chat_room_id, sender_id, content)

    def get_chat_history(self, room_id: int, user_id: int):
        chat_room = self.repo.get_chat_room_by_id(room_id)
        if not chat_room or (user_id not in [chat_room.user1_id, chat_room.user2_id]):
            raise HTTPException(status_code=403, detail="Access denied to this chat room")
        return self.repo.get_chat_history(room_id)
        
    def get_user_chat_rooms(self, user_id: int):
        return self.repo.get_user_chat_rooms(user_id)
    
    def get_chat_room_by_id(self, chat_room_id: int):
        """Fetch a chat room by ID"""
        return self.repo.get_chat_room_by_id(chat_room_id)
    
    def delete_chat_room(self, chat_room_id: int):
        """
        Delete a chat room and all associated messages.
        """
        return self.repo.delete_chat_room(chat_room_id)

    def mark_messages_as_read(self, user_id: int, chatroom_ids: List[int]):
        """
        Mark all unread messages in chat rooms as read for the authenticated user.
        """
        return self.repo.mark_messages_as_read(user_id, chatroom_ids)

    def get_other_user_id(self, room_id: int, user_id: int):
        return self.repo.get_other_user_id(room_id, user_id)