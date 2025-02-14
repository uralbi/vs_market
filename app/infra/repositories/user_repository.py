from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import select
from app.infra.database.models import UserModel, ProductModel, favorites_table
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.dtos.product import ProductDTO
from typing import List


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

    def get_favorite_products(self, user_id: int) -> List[ProductDTO]:
        """Retrieve favorite products for the user, including images."""

        stmt = (
            select(ProductModel)
            .join(favorites_table, favorites_table.c.product_id == ProductModel.id)
            .filter(favorites_table.c.user_id == user_id)
            .options(joinedload(ProductModel.images))  # Load product images
        )

        favorite_products = self.db.execute(stmt).unique().scalars().all()

        # Convert to DTOs
        return [
            ProductDTO(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                category=product.category,
                created_at=product.created_at.isoformat(),
                owner_id=product.owner_id,
                image_urls=[img.image_url for img in product.images]  # Include images
            )
            for product in favorite_products
        ]