from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import User

class IUserRepository(ABC):
    @abstractmethod
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        pass
    
    @abstractmethod
    def create_user(self, user: User) -> User:
        pass
