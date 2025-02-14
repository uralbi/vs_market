from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.infra.database.models import ProductModel, UserModel, ProductImageModel
from app.domain.dtos.product import ProductCreateDTO
from app.services.user_service import UserService
from typing import List
from app.infra.repositories.product_repository import ProductRepository
import os

class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)

    def create_product(self, user_email: str, product_data: ProductCreateDTO) -> ProductModel:
        """
        Create a new product and associate it with the user.
        """
        user_service = UserService(self.db)
        user = user_service.get_user_by_email(user_email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found!")
        elif not user.is_active:
            raise HTTPException(status_code=404, detail="User not activated!")
        
        prod_repo = ProductRepository(self.db)
                
        new_product = prod_repo.create_product(user.id, product_data) 

        return new_product
    
    def add_images_to_product(self, product_id: int, image_urls: List[str]):
        """
        Add images to an existing product.
        """
        for image_url in image_urls:
            image = ProductImageModel(product_id=product_id, image_url=image_url)
            self.db.add(image)
        
        self.db.commit()
        
    def get_all_products(self, limit: int = 10, offset: int = 0) -> List[ProductModel]:
        """
        Fetch all products from the database, ordered by latest first.
        """
        return self.product_repo.get_all_products(100, 0)

    def get_user_products(self, owner_id, limit: int = 10, offset: int = 0) -> List[ProductModel]:
        """
        Fetch all products from the database, ordered by latest first.
        """
        return self.product_repo.get_user_products(owner_id, 100, 0)
    
    def get_product_by_id(self, id: int):
        return self.product_repo.get_product_by_id(id)
    
    def delete_product(self, product_id: int):
        """ Delete a product and its associated images """
        product = self.product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Delete product and related images from DB
        self.product_repo.delete_product(product.id)
        
    def get_latest_product(self):
        return self.product_repo.get_latest_product()
