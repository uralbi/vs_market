from sqlalchemy.orm import Session
from app.infra.database.models import UserModel
from app.domain.interfaces.user_repository import IUserRepository


class UserRepository(IUserRepository):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: int) -> UserModel:
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()
    
    def get_user_by_email(self, user_email: str) -> UserModel:
        return self.db.query(UserModel).filter(UserModel.email == user_email).first()
    
    def create_user(self, user: UserModel) -> UserModel:
        self.db.add(user)
        self.db.commit()
        return user
