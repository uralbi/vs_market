from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.infra.repositories.image_repository import ProductImageRepository
from app.utils.image_processor import preprocess_image
from app.domain.dtos.product import ProductImageDTO


# router = APIRouter()

# @router.post("/upload/{product_id}", response_model=ProductImageDTO)
# async def upload_product_image(
#     product_id: int,
#     file: UploadFile = File(...),
#     db: Session = Depends(get_db)
# ):
#     """Upload an image for a product after preprocessing it."""
#     if file.content_type not in ["image/jpeg", "image/png", "image/webp"]:
#         raise HTTPException(status_code=400, detail="Only JPEG, PNG, WEBP images are allowed")

#     image_path = preprocess_image(file).replace("app/web/", "")
#     image_repo = ProductImageRepository(db)
#     image = image_repo.add_image(product_id, image_path)

#     return image
