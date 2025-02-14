from sqlalchemy.orm import Session, joinedload
from app.infra.database.models import ProductModel, ProductImageModel
from app.domain.dtos.product import ProductCreateDTO, ProductDTO
from typing import List
from sqlalchemy.orm import joinedload
import os

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_product(self, user_id: int, product_data: ProductCreateDTO) -> ProductModel:
        """Create a new product with images."""
        new_product = ProductModel(
            owner_id=user_id,
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            category=product_data.category,
        )
        self.db.add(new_product)
        self.db.commit()
        self.db.refresh(new_product)
        
        return new_product

    def get_all_products(self, limit: int, offset: int) -> List[ProductDTO]:
        """Retrieve all products with associated images."""
        products = (
                self.db.query(ProductModel)
                .options(joinedload(ProductModel.images))  # Load images in a single query
                .order_by(ProductModel.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            
        return [
                    ProductDTO(
                        id=product.id,
                        name=product.name,
                        description=product.description,
                        price=product.price,
                        category=product.category,
                        created_at=str(product.created_at),
                        owner_id=product.owner_id,
                        image_urls=[img.image_url for img in product.images]  # ✅ Images loaded in one query
                    )
                    for product in products
                ]
    
    def get_user_products(self, owner_id:int, limit: int, offset: int) -> List[ProductDTO]:
        """Retrieve all products with associated images."""
    
        products = (
                self.db.query(ProductModel)
                .filter(ProductModel.owner_id == owner_id)
                .options(joinedload(ProductModel.images))  # Load images in a single query
                .order_by(ProductModel.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
        
        return [
                    ProductDTO(
                        id=product.id,
                        name=product.name,
                        description=product.description,
                        price=product.price,
                        category=product.category,
                        created_at=str(product.created_at),
                        owner_id=product.owner_id,
                        image_urls=[img.image_url for img in product.images]  # ✅ Images loaded in one query
                    )
                    for product in products
                ]
    
    def get_product_by_id(self, product_id: int) -> ProductModel:
        """Fetch a product by id."""
        
        return (
                self.db.query(ProductModel)
                .options(joinedload(ProductModel.images))  #  Eagerly loads related images
                .filter(ProductModel.id == product_id)
                .first()
            )

    def delete_product(self, product_id: int):
        """Delete a product and its images."""
        product = self.get_product_by_id(product_id)
        
        if not product:
            return False
        
        self.db.delete(product)
        self.db.commit()
            
        # Delete images from disk before deleting from DB
        image_paths = [image.image_url for image in product.images]  # Get all image file paths

        for image_path in image_paths:
            full_path = os.path.join("app/web", image_path)  # Convert DB path to real path
            if os.path.exists(full_path):
                os.remove(full_path)  # Delete file from disk
                
        return True

    def get_latest_product(self):
        return self.db.query(ProductModel).options(joinedload(ProductModel.images)) \
                .order_by(ProductModel.created_at.desc()).first()