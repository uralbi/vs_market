from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, ForeignKey, \
                        Text, Float, Table, Index, UniqueConstraint, Computed
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from passlib.context import CryptContext
from sqlalchemy.dialects.postgresql import TSVECTOR


Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Association Table: Many-to-Many between Users & Products
favorites_table = Table(
    "favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("product_id", Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
)

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    entity = relationship("EntityModel", back_populates="creator", uselist=False, cascade="all, delete-orphan")
    
    products = relationship("ProductModel", back_populates="owner", cascade="all, delete-orphan")
    
    favorite_products = relationship("ProductModel", secondary=favorites_table, back_populates="favorited_by")
    
    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)



class EntityModel(Base):
    __tablename__ = "entities"
    
    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    entity_name = Column(String, unique=True, index=True, nullable=False)
    entity_phone = Column(String(20), unique=True, nullable=False)
    entity_address = Column(String, unique=False, nullable=True)
    entity_whatsapp = Column(String(20), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    creator = relationship("UserModel", back_populates="entity")


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    is_dollar = Column(Boolean, default=False, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("UserModel", back_populates="products")

    # One-to-Many Relationship with Images
    images = relationship("ProductImageModel", back_populates="product", cascade="all, delete")

    favorited_by = relationship("UserModel", secondary=favorites_table, back_populates="favorite_products")

    search_vector = Column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('russian', coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(category, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(name, '') || ' ' || coalesce(description, '') || ' ' || coalesce(category, '')), 'B')",
            persisted=True
        )
    )

    __table_args__ = (
        Index("idx_products_search", search_vector, postgresql_using="gin"), # Vector match search
        Index("idx_products_exact_match", "name", "description", "category", 
              func.lower("name"),
              func.lower("description"),
              func.lower("category"),
              postgresql_using="btree"),  # Exact match index
        Index("idx_products_trgm", "name", "description", "category", postgresql_using="gin"),  # Trigram search
        UniqueConstraint('name', 'owner_id', name='uix_owner_product_name'),
    )
    
class ProductImageModel(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(String(500), nullable=False)

    product = relationship("ProductModel", back_populates="images")
