from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict
from app.infra.database.db import get_db
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from typing import Dict


class ChatConsumer:
    active_connections: Dict[int, WebSocket] = {}
    user_map: Dict[int, str] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int, db: Session):
        """Accepts WebSocket connection and stores the user."""
        
        await websocket.accept()
        self.active_connections[user_id] = websocket
        
        user_service = UserService(db)
        user = user_service.get_user_by_id(user_id)
        if user:
            self.user_map[user_id] = user.username
        else:
            await websocket.close(code=1003, reason="User not found.")
            del self.active_connections[user_id]
            return

    async def disconnect(self, user_id: int):
        """Removes the user from active connections."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected.")

    async def receive_message(self, websocket: WebSocket, user_id: int, subject: str, db):
        """Listens for messages, saves them, and forwards them to the receiver."""
        try:
            while True:
                data = await websocket.receive_json()
                receiver_id = data.get("receiver_id")
                message_content = data.get("message")
                sender_username = self.user_map.get(user_id, f"User-{user_id}")  # Fallback if not found

                chat_service = ChatService(db)
                chat_room = chat_service.get_or_create_chat_room(user_id, receiver_id, subject)
                chat_service.save_message(chat_room.id, user_id, message_content)
                if receiver_id in self.active_connections:
                    await self.active_connections[receiver_id].send_json({
                        "sender_id": user_id,
                        "sender_username": sender_username,
                        "message": message_content
                    })
        except WebSocketDisconnect:
            await self.disconnect(user_id)

