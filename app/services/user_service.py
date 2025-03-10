from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.domain.entities.user import User
from app.domain.dtos.user import UserRegistrationDTO
from app.infra.database.models import UserModel
from app.infra.tasks.email_tasks import send_verification_email, send_notification_email
from app.domain.security.auth_token import create_access_token
from app.domain.security.get_hash import get_password_hash
from app.infra.repositories.user_repository import UserRepository
from app.domain.dtos.product import ProductDTO
from app.infra.database.models import UserRole
from fastapi import HTTPException
from typing import List, Optional
from app.core.config import settings


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def register_user(self, user_data: UserRegistrationDTO) -> User:
        """Registers a new user, handling unique constraint errors."""
        
        # ✅ Check if email already exists
        existing_user = self.db.query(UserModel).filter(UserModel.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Такой аккаунт уже существует!")

        hashed_password = get_password_hash(user_data.password)

        db_user = UserModel(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=False
        )

        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
        except IntegrityError as e:
            self.db.rollback()
            error_message = str(e.orig)

            if "ix_users_username" in error_message:  # ✅ Username unique constraint
                raise HTTPException(status_code=400, detail="Такое имя пользователя уже существует")
            elif "ix_users_email" in error_message:  # ✅ Email unique constraint
                raise HTTPException(status_code=400, detail="Эл. почта уже была зарегистрирована")
            else:
                raise HTTPException(status_code=500, detail="Ошибка при регистрации")

        self.send_activation_email(db_user.email)

        return User(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            is_active=db_user.is_active,
            created_at=db_user.created_at
        )

    def get_user_by_email(self, email: str) -> UserModel:
        """Retrieves a user by email."""
        return self.repo.get_user_by_email(email)

    def get_user_by_id(self, user_id: int) -> UserModel:
        """Retrieves a user by ID."""
        return self.repo.get_user_by_id(user_id)
        
    def get_user_by_username(self, username: str) -> UserModel:
        """Retrieves a user by username."""
        return self.db.query(UserModel).filter(UserModel.username == username).first()
    
    def update_username(self, user: UserModel, new_username: str):
        """Update user's username with uniqueness check."""
        if self.db.query(UserModel).filter(UserModel.username == new_username).first():
            raise HTTPException(status_code=400, detail="Такое имя пользователя уже существует")
        try:
            user.username = new_username
            self.db.commit()
            self.db.refresh(user)
        except Exception:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при обновлении имени пользователя")

    def update_password(self, user: UserModel, new_password: str):
        """Update user's password with hashing."""
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        body = "Ваш пароль изменен!"
        send_notification_email.delay(user.email, body)

    def update_email(self, user: UserModel, new_email: str):
        """Update user's email."""
        oldemail = user.email
        user.email = new_email
        
        try:
            self.db.commit()
            self.db.refresh(user)
            message_body = f"Эл. почта для вашего аккаунта в iMarket изменен на {new_email}!"
            send_notification_email.delay(oldemail, message_body)
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Эл. почта уже существует")
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Ошибка обновления почты")
        

    def send_activation_email(self, email: str):
        acc_token = create_access_token({"sub": email})
        verification_link = f"{settings.DOMAIN}/api/auth/verify-email?token={acc_token}"
        send_verification_email.delay(email, verification_link)
    
    def get_favorites(self, user_id: int) -> List[ProductDTO]:
        """Get a user's favorite products with images."""
        return self.repo.get_favorite_products(user_id)
    
    def deactivate_user(self, user_id: int):
        user = self.repo.get_user_by_id(user_id)
        if not user:
            return HTTPException(status_code=404, detail="User Not Found")
        message_body = f"Ваш аккаунт iBer.kg ({user.email}) деактивирован."
        send_notification_email.delay(user.email, message_body)
        return self.repo.deactivate_user(user_id)
    
    def activate_user(self, user_id: int):
        user = self.repo.get_user_by_id(user_id)
        if not user:
            return HTTPException(status_code=404, detail="User Not Found")
        message_body = f"Ваш аккаунт iBer.kg ({user.email}) активирован."
        send_notification_email.delay(user.email, message_body)
        return self.repo.activate_user(user_id)
    
    def get_all_users(self, limit: int, offset: int, 
                      email: Optional[str]=None, is_active: Optional[bool]=None) -> List[UserModel]:
        """ Fetch all users by email or is_active """
        query = self.repo.get_all_users().filter(UserModel.role != 'ADMIN')
        
        if email:
            query = query.filter(UserModel.email.ilike(f"%{email}%"))

        if is_active is not None:
            query = query.filter(UserModel.is_active == is_active)

        return query.offset(offset).limit(limit).all()

    def add_to_favorites(self, product, user):
        return self.repo.add_to_favorites(product, user)
    
    def remove_from_favorites(self, product, user):
        return self.repo.remove_from_favorites(product, user)
    
    def update_user_role(self, user_id: int, user_role: UserRole):
        user = self.repo.get_user_by_id(user_id)
        body = f"Ваш статус изменен на: {user_role.value}"
        send_notification_email.delay(user.email, body)
        return self.repo.update_user_role(user_id, user_role)
        