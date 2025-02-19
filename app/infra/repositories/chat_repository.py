from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import or_
from app.infra.database.models import ChatRoom, Message, UserModel
from datetime import datetime
from typing import List


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_chat_room(self, user1_id: int, user2_id: int) -> ChatRoom:
        """Retrieve an existing chat room between two users or create a new one."""
        chat_room = (
            self.db.query(ChatRoom)
            .filter(
                or_(
                    (ChatRoom.user1_id == user1_id) & (ChatRoom.user2_id == user2_id),
                    (ChatRoom.user1_id == user2_id) & (ChatRoom.user2_id == user1_id),
                )
            )
            .first()
        )
        if not chat_room:
            chat_room = ChatRoom(user1_id=user1_id, user2_id=user2_id)
            self.db.add(chat_room)
            self.db.commit()
            self.db.refresh(chat_room)

        return chat_room

    def save_message(self, chat_room_id: int, sender_id: int, content: str) -> Message:
        """Save a new message in the chat room."""
        message = Message(chat_room_id=chat_room_id, sender_id=sender_id, content=content, timestamp=datetime.utcnow())
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_chat_history(self, user1_id: int, user2_id: int):
        """Retrieve chat history including sender usernames, only if the chat room exists."""

        chat_room = (
            self.db.query(ChatRoom)
            .filter(
                ((ChatRoom.user1_id == user1_id) & (ChatRoom.user2_id == user2_id)) |
                ((ChatRoom.user1_id == user2_id) & (ChatRoom.user2_id == user1_id))
            )
            .first()
        )

        if not chat_room:
            return []  # Return empty list if chat room doesn't exist

        # Step 2: Fetch messages along with sender usernames
        messages = (
            self.db.query(
                Message.sender_id,
                UserModel.username,  # ✅ Fetch username
                Message.content,
                Message.timestamp
            )
            .join(UserModel, UserModel.id == Message.sender_id)  
            .filter(Message.chat_room_id == chat_room.id) 
            .order_by(Message.timestamp.asc())  
            .all()
        )

        return messages  # ✅ Returns list of tuples: (sender_id, sender_username, content, timestamp)


    def get_user_chat_rooms(self, user_id: int):
        """Fetch all chat rooms where the user is a participant."""
        return (
            self.db.query(ChatRoom)
            .filter(UserModel.id != user_id)
            .filter((ChatRoom.user1_id == user_id) | (ChatRoom.user2_id == user_id))
            .join(UserModel, 
                  (ChatRoom.user1_id == UserModel.id) | (ChatRoom.user2_id == UserModel.id)
                  )
            .all()
        )
    
    def get_chat_room_by_id(self, chat_room_id: int):
        """Fetch a chat room by ID"""
        return self.db.query(ChatRoom).filter(ChatRoom.id == chat_room_id).first()

    def delete_chat_room(self, chat_room):
        """Delete a chat room and cascade delete its messages"""
        self.db.delete(chat_room)
        self.db.commit()