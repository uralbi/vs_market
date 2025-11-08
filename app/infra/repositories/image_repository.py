from sqlalchemy.orm import Session
from app.infra.database.models import ProductImageModel


class ProductImageRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_image(self, product_id: str, image_url: str):
        """Attach an image to a product."""
        image = ProductImageModel(product_id=product_id, image_url=image_url)
        self.db.add(image)
        self.db.commit()
        return image

    def get_images_by_product(self, product_id: str):
        """Get all images for a given product."""
        return self.db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).all()

    def delete_images_by_product(self, product_id: str):
        """Delete all images associated with a product."""
        self.db.query(ProductImageModel).filter(ProductImageModel.product_id == product_id).delete()
        self.db.commit()
