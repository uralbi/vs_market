from sqlalchemy import Column, Integer, String, DateTime, Boolean, func, ForeignKey, \
                        Text, Float, Table, Index, UniqueConstraint, Computed
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from passlib.context import CryptContext
from sqlalchemy.dialects.postgresql import TSVECTOR
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    USER = "USER"

    
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class MovieModel(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True, unique=True)
    description = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)  # Path to the actual video file
    thumbnail_path = Column(String(500), nullable=True)  # Thumbnail image
    duration = Column(Float, nullable=True)  # Duration in seconds
    is_public = Column(Boolean, default=True, nullable=False)  # Whether movie is public
    created_at = Column(DateTime, default=datetime.now)
    price = Column(Float, nullable=False, default=100)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("UserModel", back_populates="movies")

    views = relationship("MovieViewModel", back_populates="movie", cascade="all, delete-orphan")
    likes = relationship("MovieLikeModel", back_populates="movie", cascade="all, delete-orphan")
    comments = relationship("MovieCommentModel", back_populates="movie", cascade="all, delete-orphan")
    subtitles = relationship("MovieSubtitleModel", back_populates="movie", cascade="all, delete-orphan")
    orders = relationship("OrderModel", back_populates="video", cascade="all, delete-orphan")
    
    search_vector = Column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '')), 'A') || "
            "setweight(to_tsvector('russian', coalesce(title, '') || ' ' || coalesce(description, '')), 'B')",
            persisted=True
        )
    )

    __table_args__ = (
        Index("idx_movies_search", search_vector, postgresql_using="gin"),  # GIN index for fast searching
    )
    

class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    status = Column(ENUM("PENDING", "COMPLETED", "FAILED", name="order_status"), default="PENDING")
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("UserModel", back_populates="orders")
    movie = relationship("MovieModel", back_populates="orders")


class MovieViewModel(Base):
    __tablename__ = "movie_views"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who watched
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)  # Movie being watched
    watched_at = Column(DateTime, default=datetime.now)  # Timestamp of watch
    progress = Column(Float, default=0)  # Last watched time in seconds

    movie = relationship("MovieModel", back_populates="views")


class MovieCommentModel(Base):
    __tablename__ = "movie_comments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Commenting user
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)  # Movie
    content = Column(Text, nullable=False)  # Comment content
    posted_at = Column(DateTime, default=datetime.utcnow)  # Timestamp

    movie = relationship("MovieModel", back_populates="comments")


class MovieSubtitleModel(Base):
    __tablename__ = "movie_subtitles"

    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)  # Movie
    language = Column(String(50), nullable=False)  # Language (e.g., "English", "Spanish")
    file_path = Column(String(500), nullable=False)  # Subtitle file path

    movie = relationship("MovieModel", back_populates="subtitles")


class MovieLikeModel(Base):
    __tablename__ = "movie_likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who liked
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)  # Liked movie
    liked_at = Column(DateTime, default=datetime.utcnow)  # Timestamp

    movie = relationship("MovieModel", back_populates="likes")


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"))
    user2_id = Column(Integer, ForeignKey("users.id"))

    user1 = relationship("UserModel", foreign_keys=[user1_id])
    user2 = relationship("UserModel", foreign_keys=[user2_id])
    messages = relationship("Message", back_populates="chat_room", cascade="all, delete")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_room_id = Column(Integer, ForeignKey("chat_rooms.id"))
    sender_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    
    chat_room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("UserModel", foreign_keys=[sender_id])


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
    
    role = Column(
        ENUM(UserRole, name="userrole", create_type=False), 
        default=UserRole.USER,
        nullable=False
    )
    
    entity = relationship("EntityModel", back_populates="creator", uselist=False, cascade="all, delete-orphan")
    products = relationship("ProductModel", back_populates="owner", cascade="all, delete-orphan")
    favorite_products = relationship("ProductModel", secondary=favorites_table, back_populates="favorited_by")
    movies = relationship("MovieModel", back_populates = "owner", cascade="all, delete-orphan"    )
    
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
    description = Column(Text, nullable=False)
    price = Column(Float, nullable=False)
    is_dollar = Column(Boolean, default=False, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activated = Column(Boolean, default=True, nullable=False, index=True)
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
