from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.infra.database.models import ProductModel, UserModel, ProductImageModel
from app.domain.dtos.product import ProductCreateDTO, ProductDTO
from app.services.user_service import UserService
from app.services.image_service import ImageService
from typing import List
from app.infra.repositories.product_repository import ProductRepository


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
                
        new_product = self.product_repo.create_product(user.id, product_data) 

        return new_product
    
    def add_images_to_product(self, product_id: int, image_urls: List[str]):
        """
        Add images to an existing product.
        """
        for image_url in image_urls:
            image = ProductImageModel(product_id=product_id, image_url=image_url)
            self.db.add(image)
        
        self.db.commit()
        
    def get_all_products(self, limit: int = 100, offset: int = 0) -> List[ProductModel]:
        """
        Fetch all products from the database, ordered by latest first.
        """
        return self.product_repo.get_all_products(limit, offset)

    def get_user_products(self, owner_id, limit: int = 10, offset: int = 0) -> List[ProductModel]:
        """
        Fetch all products from the database, ordered by latest first.
        """
        return self.product_repo.get_user_products(owner_id, 100, 0)
    
    def get_product_by_id(self, id: int, user=None):
        product = self.product_repo.get_product_by_id(id)
        
        if not product:
            raise HTTPException(status_code=404, detail="Item not found")
        if product.activated:
            return product
        if user and product.owner_id == user.id:
            return product
        return HTTPException(status_code=404, detail="Item not found")
        
    def delete_product(self, product_id: int, user):
        """ Delete a product and its associated images """
        product = self.product_repo.get_product_by_id(product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Delete product and related images from DB
        self.product_repo.delete_product(product.id, user)
        
    def get_latest_product(self):
        return self.product_repo.get_latest_product()

    def update_product(self, product_id: int, user, updated_data: dict) -> ProductModel:
        # check if product owner is user
        return self.product_repo.update_product(product_id, updated_data)

    def update_product_images(self, product_id: int, image_urls: List[str], keep_existing: bool = True):
       
        return self.product_repo.update_product_images(product_id, image_urls, keep_existing)

    def search(self, query: str, limit: int, offset: int) -> List[ProductDTO]:
        """ Exact Search first if not then make full-text search """
        results = self.product_repo.full_text_search(query, limit, offset)
        results2 = self.product_repo.exact_search(query, limit, offset)
        seen = set()
        final_results = []

        for product in results + results2:
            if product.id not in seen:
                seen.add(product.id)
                final_results.append(product)
        
        return self._map_products_with_images(final_results)
    
    def full_text_search(self, query: str, limit: int, offset: int) -> List[ProductDTO]:
        """ Full-Text Search using PostgreSQL tsquery """
        products = self.product_repo.full_text_search(query, limit, offset)
        return self._map_products_with_images(products)

    def exact_search(self, query: str, limit: int, offset: int) -> List[ProductDTO]:
        """ Exact Match Search for product name, description, and category """
        products = self.product_repo.exact_search(query, limit, offset)
        return self._map_products_with_images(products)
    
    def _map_products_with_images(self, products: List[ProductModel]) -> List[ProductDTO]:
        """ Helper function to map products with their images """
        result = []
        for product in products:
            image_urls = [img.image_url for img in product.images]
            
            result.append(ProductDTO(
                id=product.id,
                name=product.name,
                description=product.description,
                price=product.price,
                category=product.category,
                created_at=str(product.created_at),
                owner_id=product.owner_id,
                image_urls=image_urls
            ))
        return result

    def deactivate_user_products(self, user_id):
        # todo remove from favorites.
        return self.product_repo.deactivate_user_products(user_id)