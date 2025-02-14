from fastapi import Request, Depends
from app.services.user_service import UserService
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.utils.auth import get_current_user  # Function to get logged-in user from token


def global_context(request: Request, db: Session = Depends(get_db)):
    """
    Provides global context to all Jinja2 templates.
    """
    user = None
    if "access_token" in request.cookies:
        token = request.cookies.get("access_token")
        user_service = UserService(db)
        user = get_current_user(token, user_service)

    return {"request": request, "current_user": user}
