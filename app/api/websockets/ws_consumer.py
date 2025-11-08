from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict
from app.infra.database.db import get_db
from app.infra.database.models import UserModel
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from typing import Dict


class ChatConsumer:
    active_connections: Dict[str, WebSocket] = {}
    user_map: Dict[str, str] = {}
    
    async def connect(self, websocket: WebSocket, user: UserModel, receiver_id: str, db: Session):
        """Accepts WebSocket connection and stores the user."""
        
        print(f"User {user.username} connecting to chat with receiver {receiver_id}")
        await websocket.accept()
        self.active_connections[user.id] = websocket
        
        await self.notify_other_user_status(user.id, True)
        
        is_receiver_online = receiver_id in self.active_connections
        await websocket.send_json({"user_id": receiver_id, "is_online": is_receiver_online})
    
        if user:
            self.user_map[user.id] = user.username
        else:
            await websocket.close(code=1003, reason="User not found.")
            del self.active_connections[user.id]
            return

    async def disconnect(self, user_id: str):
        """Removes the user from active connections."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        await self.notify_other_user_status(user_id, False)

    async def receive_message(self, websocket: WebSocket, user_id: str, subject: str, db):
        """Listens for messages, saves them, and forwards them to the receiver."""
        try:
            while True:
                data = await websocket.receive_json()
                receiver_id = data.get("receiver_id")
                message_content = data.get("message")
                sender_username = self.user_map.get(user_id, f"User-{user_id}")  # Fallback if not found
                chat_service = ChatService(db)
                chat_room = chat_service.get_or_create_chat_room(user_id, receiver_id, subject)
                is_online = receiver_id in self.active_connections
                if is_online:
                    chat_service.save_and_mark_messages_as_read(chat_room.id, user_id, message_content)
                    await self.active_connections[receiver_id].send_json({
                        "sender_id": user_id,
                        "sender_username": sender_username,
                        "message": message_content
                    })
                else:
                    chat_service.save_message(chat_room.id, user_id, message_content)
                
        except WebSocketDisconnect:
            await self.disconnect(user_id)

    async def notify_other_user_status(self, user_id: str, is_online: bool):
        """Send online/offline status to the counterpart only."""
        for other_user_id, conn in self.active_connections.items():
            if other_user_id != user_id:  # Only notify the other user
                await conn.send_json({
                    "user_id": user_id,
                    "is_online": is_online
                })