from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, Query
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from typing import List
from app.infra.database.db import get_db
from app.domain.dtos.product import ProductDTO, ProductCreateDTO
from app.services.product_service import ProductService
from app.services.image_service import ImageService
from app.services.user_service import UserService
from app.domain.security.auth_token import decode_access_token
import asyncio, json
import redis.asyncio as redis


router = APIRouter(
    prefix='/api/products',
    tags=['Products']
)

REDIS_URL = "redis://localhost:6379"
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.get("/search", response_model=List[ProductDTO])
async def search_products(
    db: Session = Depends(get_db),
    query: str = Query(..., min_length=2, description="Search query"),
    limit: int = 100,
    offset: int = 0,
):
    """
    Search products by name, description, and category using Full-Text Search.
    """

    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Search term must be more then 2 characters")
    
    # Generate cache key
    cache_key = f"search:{query}:{limit}:{offset}"

    # Check if result exists in cache
    cached_results = await redis_client.get(cache_key)
    if cached_results:
        return json.loads(cached_results)
    
    product_service = ProductService(db)
    results = product_service.search(query, limit, offset)
    
    # Store result in Redis (expires in 1 hour 3600 secs)
    serialized_results = [r.model_dump(mode="json") for r in results]
    await redis_client.setex(cache_key, 60, json.dumps(serialized_results))
    
    return results

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
    images: List[UploadFile] = File(None),  # ✅ Accept multiple images
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
    
    if images or len(images) > 0:
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


@router.put("/update/{product_id}", response_model=ProductDTO)
async def update_product(
        product_id: int,
        name: str = Form(None),
        description: str = Form(None),
        price: float = Form(None),
        category: str = Form(None),
        images: List[UploadFile] = File(None),  # Optional images
        token: str = Depends(token_scheme),
        db: Session = Depends(get_db)
    ):
    """
    Update an existing product. Only the product owner can update it.
    """
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    product_service = ProductService(db)
    user_service = UserService(db)
    
    # Verify user exists
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch existing product
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Ensure the user owns the product
    if product.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this product")

    # Update only provided fields
    updated_data = {
        "name": name or product.name,
        "description": description or product.description,
        "price": price if price is not None else product.price,
        "category": category or product.category,
    }

    # Update images (if new ones are uploaded)
    if images:
        image_service = ImageService()
        image_urls = [await image_service.process_and_store_image(image) for image in images]
        product_service.update_product_images(product_id, image_urls)

    # Update product in DB
    updated_product = product_service.update_product(product_id, updated_data)

    return updated_product


@router.get("/{product_id}", response_model=ProductDTO)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Fetch product details by ID."""
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_dto = ProductDTO.model_validate(product)
    product_dto.image_urls = [img.image_url for img in product.images]
    
    return product_dto
