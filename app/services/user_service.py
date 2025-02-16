from sqlalchemy.orm import Session
from app.domain.entities.user import User
from app.domain.dtos.user import UserRegistrationDTO
from app.infra.database.models import UserModel
from app.infra.tasks.email_tasks import send_verification_email, send_notification_email
from app.domain.security.auth_token import create_access_token
from app.domain.security.get_hash import get_password_hash
from app.infra.repositories.user_repository import UserRepository
from app.domain.dtos.product import ProductDTO
from fastapi import HTTPException
from typing import List


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = UserRepository(db)

    def register_user(self, user_data: UserRegistrationDTO) -> User:
        """Registers a new user."""
        
        existing_user = self.db.query(UserModel).filter(UserModel.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = get_password_hash(user_data.password)

        db_user = UserModel(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            is_active=False
        )
        
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

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
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_user_by_username(self, username: str) -> UserModel:
        """Retrieves a user by username."""
        return self.db.query(UserModel).filter(UserModel.username == username).first()
    
    def update_password(self, user: UserModel, new_password: str):
        """Update user's password with hashing."""
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        self.db.refresh(user)
        body = "Your Password is Changed!"
        send_notification_email.delay(user.email, body)

    def update_email(self, user: UserModel, new_email: str):
        """Update user's email."""
        oldemail = user.email
        user.email = new_email
        self.db.commit()
        self.db.refresh(user)
        message_body = "This EMAIL is changed for authentication to our Account!"
        send_notification_email.delay(oldemail, message_body)

    def send_activation_email(self, email: str):
        acc_token = create_access_token({"sub": email})
        verification_link = f"http://127.0.0.1:8000/api/auth/verify-email?token={acc_token}"
        send_verification_email.delay(email, verification_link)
    
    def deactivate_user(self, email:str):
        user = self.get_user_by_email(email)
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        
        message_body = f"Your account ({email}) deactivate, and will be deleted in 30 days."
        send_notification_email.delay(email, message_body)
    
    def get_favorites(self, user_id: int) -> List[ProductDTO]:
        """Get a user's favorite products with images."""
        return self.repo.get_favorite_products(user_id)
    
    def deactivate_user_products(self, user_id: int):
        return self.repo.deactivate_user_products(user_id)