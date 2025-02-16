from app.domain.security.auth_token import decode_access_token
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.user_service import UserService
from app.core.config import settings
import logging
import logging.config


logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


def user_authorization(token:str, db: Session):
    """ Autorize user. Returns user or raises HTTPException """
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_service = UserService(db)
        user = user_service.get_user_by_email(email)

        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="User not found or inactive")
        return user
    except Exception as e:
        user = None
        logger.error(f"User auth error: {e}") 
        raise HTTPException(status_code=401, detail="Invalid token")
