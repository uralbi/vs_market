from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Generator
from app.infra.database.db import get_db
from app.domain.dtos.product import ProductDTO, ProductCreateDTO
from app.services.product_service import ProductService
from app.services.image_service import ImageService
from app.services.user_service import UserService
from app.domain.security.auth_token import decode_access_token
import asyncio, json, time


router = APIRouter(
    prefix='/api/products',
    tags=['Products']
)

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.get("/sse_products")
def product_stream(db: Session = Depends(get_db)):
    """SSE endpoint to send new product updates in real-time"""

    async def event_generator():
        last_product_id = None
        product_service = ProductService(db)

        while True:
            latest_product = product_service.get_latest_product()
            if latest_product and latest_product.id != last_product_id:
                last_product_id = latest_product.id
                product_data = ProductDTO.model_validate(latest_product).model_dump()
                product_data["created_at"] = product_data["created_at"].isoformat()
                product_data["image_urls"] = [img.image_url for img in latest_product.images]
                yield f"data: {json.dumps(product_data)}\n\n"

            await asyncio.sleep(5)  # ✅ Synchronous sleep (fixes coroutine error)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.delete("/delete/{product_id}")
async def delete_product(
    product_id: int,
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)):
    """
    Delete a product. Only the owner of the product can delete it.
    """
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    if not user or not user.is_active:
        raise HTTPException(status_code=404, detail="User not found")

    # ✅ Validate product ownership
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this product")

    # Delete product images in product service
    # Delete product from database
    product_service.delete_product(product_id)

    return {"message": "Product deleted successfully"}

    
@router.post("/create", response_model=ProductDTO)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    images: List[UploadFile] = File(...),  # ✅ Accept multiple images
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    Create a new product. Only authenticated users can add a product.
    """
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    product_service = ProductService(db)

    product_data = ProductCreateDTO(
        name=name, 
        description=description, 
        price=price, 
        category=category,
    )
 
    # Create product
    new_product = product_service.create_product(email, product_data)
    
    img_service = ImageService()
    image_urls = [await img_service.process_and_store_image(image) for image in images] # Process and store images
    product_service.add_images_to_product(new_product.id, image_urls) # Associate images with product
        
    return new_product


@router.get("/mylist", response_model=List[ProductDTO])
def get_products_my_list(token: str = Depends(token_scheme), db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    """
    Get a list of products, sorted by latest first.
    """
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_service = UserService(db)
    user = user_service.get_user_by_email(email)    
    product_service = ProductService(db)
    return product_service.get_user_products(user.id, limit, offset)

@router.get("/list", response_model=List[ProductDTO])
def get_products_list(db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    """
    Get a list of products, sorted by latest first.
    """
    product_service = ProductService(db)
    return product_service.get_all_products(limit, offset)
