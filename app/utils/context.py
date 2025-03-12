from fastapi import Request, Depends
from app.services.user_service import UserService
from app.services.chat_service import ChatService
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.utils.auth import get_current_user
from app.domain.security.auth_token import create_access_token, verify_refresh_token


def global_context(request: Request, db: Session = Depends(get_db)):
    """
    Provides global context to all Jinja2 templates.
    """
    user = None
    access_token = request.cookies.get("access_token")
    refresh_token = request.cookies.get("refresh_token")
    user_service = UserService(db)

    if access_token:
        try:
            user = get_current_user(access_token, user_service)
        except Exception:
            user = None

    # If access token is missing/invalid, try refreshing
    if not user and refresh_token:
        try:
            refresh_payload = verify_refresh_token(refresh_token)
            new_access_token = create_access_token({"sub": refresh_payload["sub"]})
            response = request.state.response  # Get FastAPI response object
            response.set_cookie(
                key="access_token",
                value=new_access_token,
                httponly=True,
                secure=True,
                samesite="Strict"
            )
            user = get_current_user(new_access_token, user_service)
        except Exception:
            user = None

    # get count of chat_rooms where user's messages are not read 
    count = 0
    rooms = []
    if user:
        chat_service = ChatService(db)
        count = chat_service.get_unread_chat_rooms(user.id)
        my_chrooms = chat_service.get_user_chat_rooms(user.id)
        count = sum(1 for r in my_chrooms if r['has_unread_messages'])
        room_ids = [{"room_id":i["chat_room_id"], "username": i["other_user_username"]} for i in my_chrooms if i["has_unread_messages"]]
        last_message = [chat_service.get_chat_history(int(i["room_id"]), user.id) for i in room_ids]
        if room_ids:
            for rids, lmsg in zip(room_ids, last_message):
                messages = []
                lasttime = ""
                for msg in lmsg[-2:]:
                    messages.append(msg[2])
                    lasttime = msg[3]
                rooms.append([rids['room_id'], rids['username'], messages, lasttime])
    rooms.sort(key=lambda x: x[3], reverse=True)
    return {"request": request, "current_user": user, 'unread_rooms': count, "rooms": rooms}
