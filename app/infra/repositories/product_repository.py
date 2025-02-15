from sqlalchemy.orm import Session, joinedload
from app.infra.database.models import ProductModel, ProductImageModel
from app.domain.dtos.product import ProductCreateDTO, ProductDTO
from typing import List, Optional
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import text
from sqlalchemy import and_, or_
from app.utils.img_delete import delete_images_from_disk

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
                .options(joinedload(ProductModel.images))
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
        delete_images_from_disk(image_paths)                
        return True

    def get_latest_product(self):
        return self.db.query(ProductModel).options(joinedload(ProductModel.images)) \
                .order_by(ProductModel.created_at.desc()).first()
    
    def update_product(self, product_id: int, updated_data: dict) -> Optional[ProductModel]:
        """Update product details."""
        product = self.get_product_by_id(product_id)
        if not product:
            return None

        for key, value in updated_data.items():
            setattr(product, key, value)  # Dynamically update fields

        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product_images(self, product_id: int, image_urls: List[str]):
        """Replace images for a product."""
        
        old_images = self.db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).all()
        delete_images_from_disk(old_images)
        
        self.db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).delete()

        for image_url in image_urls:
            image = ProductImageModel(product_id=product_id, image_url=image_url)
            self.db.add(image)

        self.db.commit()
        
    def full_text_search(self, query: str, limit: int, offset: int) -> List[ProductModel]:
        """ Full-Text Search using PostgreSQL tsquery """
        
        query = " & ".join(query.split())
        
        return (
            self.db.query(ProductModel)
            .filter(
                ProductModel.search_vector.op("@@")(
                    text(f"(to_tsquery('russian', '{query}') || to_tsquery('english', '{query}'))::tsquery")
                    )
                )
            .options(joinedload(ProductModel.images))  # Load images
            .order_by(ProductModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def exact_search(self, query: str, limit: int, offset: int) -> List[ProductModel]:
        """ Exact Match Search for product name, description, and category """
        
        words = query.split()
        return (
            self.db.query(ProductModel)
            .filter(
                or_(
                and_(*(ProductModel.name.ilike(f"%{word}%") for word in words)),  # Match exact words in name
                and_(*(ProductModel.description.ilike(f"%{word}%") for word in words)),  # Match exact words in description
                and_(*(ProductModel.category.ilike(f"%{word}%") for word in words) ) # Match exact words in category
                )
            )
            .options(joinedload(ProductModel.images))  # Load images
            .order_by(ProductModel.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )