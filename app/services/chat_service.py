from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.infra.repositories.chat_repository import ChatRepository


class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ChatRepository(db)

    def get_or_create_chat_room(self, user1_id: int, user2_id: int):
        print('creating a chart room:', user1_id, user2_id)
        if user1_id == user2_id:
            raise HTTPException(status_code=403, detail="No counterport")
        return self.repo.get_or_create_chat_room(user1_id, user2_id)

    def save_message(self, chat_room_id: int, sender_id: int, content: str):
        return self.repo.save_message(chat_room_id, sender_id, content)

    def get_chat_history(self, user1_id: int, user2_id: int):
        return self.repo.get_chat_history(user1_id, user2_id)
        
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