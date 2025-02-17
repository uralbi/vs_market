from sqlalchemy.orm import Session
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

    def get_chat_history(self, chat_room_id: int) -> List[Message]:
        """Retrieve all messages from a chat room."""
        return (
            self.db.query(
                Message.sender_id,
                UserModel.username,
                Message.content,
                Message.timestamp
            )
            .filter(Message.chat_room_id == chat_room_id)
            .join(UserModel, Message.sender_id == UserModel.id)  # Join messages with users
            .order_by(Message.timestamp.asc())
            .all()
        )

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