from app.domain.security.auth_token import decode_access_token
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from app.infra.database.models import UserModel
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
            raise HTTPException(status_code=401, detail="Не верный Токен!, Необходимо Войти заново.")

        user_service = UserService(db)
        user = user_service.get_user_by_email(email)

        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="Аккаунт не найден или деактивирован")
        return user
    except Exception as e:
        user = None
        logger.error(f"User auth error: {e}") 
        raise HTTPException(status_code=401, detail="Неверный Токен")


def user_creator_auth(user: UserModel) -> bool:
    """
    Authorization for ADMIN, CREATOR.
    """
    if user.role not in ["ADMIN", "CREATOR"]:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def user_manager_auth(user: UserModel) -> bool:
    """
    Authorization for ADMIN, MANAGER.
    """
    if user.role not in ["ADMIN", "MANAGER"]:
        return False
        # raise HTTPException(status_code=401, detail="Unauthorized")
    return True

def user_admin_auth(user: UserModel) -> bool:
    """
    Authorization for ADMIN.
    """
    if user.role != "ADMIN":
        return False
    return True