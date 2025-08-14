from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql import select
from app.infra.database.models import UserModel, ProductModel, favorites_table
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.dtos.product import ProductDTO
from typing import List, Optional


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
                is_dollar=product.is_dollar,
                image_urls=[img.image_url for img in product.images]  # Include images
            )
            for product in favorite_products
        ]
    
    def get_all_users(self):
        """
        Fetch all users with.
        """
        return self.db.query(UserModel)

    def deactivate_user(self, user_id: int):
        self.db.query(UserModel).filter(UserModel.id == user_id).update({"is_active": False})
        self.db.commit()

    
    def activate_user(self, user_id: int):
        query = self.db.query(UserModel).filter(UserModel.id == user_id).update({"is_active": True})
        self.db.commit()
        return query
    
    def add_to_favorites(self, product, user):
        if product not in user.favorite_products:
            user.favorite_products.append(product)
            self.db.commit()
            self.db.refresh(user)

    def remove_from_favorites(self, product, user):
        if product in user.favorite_products:
            user.favorite_products.remove(product)
            self.db.commit()
            self.db.refresh(user)
    
    def update_user_role(self, user_id: int, user_role):
        user = self.get_user_by_id(user_id)
        user.role = user_role
        self.db.commit()
        self.db.refresh(user)