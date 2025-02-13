from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from passlib.context import CryptContext

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    entity = relationship("EntityModel", back_populates="creator", uselist=False, cascade="all, delete-orphan")
    
    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)



class EntityModel(Base):
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    entity_name = Column(String, unique=True, index=True, nullable=False)
    entity_phone = Column(String(20), unique=True, nullable=False)
    entity_address = Column(String, unique=False, nullable=True)
    entity_whatsapp = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    creator = relationship("UserModel", back_populates="entity")
