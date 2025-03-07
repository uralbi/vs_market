from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from app.infra.database.db import get_db
from app.domain.dtos.product import ProductDTO, ProductCreateDTO
from app.services.product_service import ProductService
from app.services.image_service import ImageService
from app.services.fav_service import FavService
# from app.infra.kafka.kafka_producer import send_kafka_message
from app.infra.redis_fld.redis_config import redis_client
import asyncio, json, os

from app.domain.security.auth_user import user_authorization

import logging
import logging.config
from app.core.config import settings
logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


router = APIRouter(
    prefix='/api/products',
    tags=['Products']
)


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
    
    # send_kafka_message(
    #     topic="product_search",
    #     key="search",
    #     message={"query": query, "timestamp": str(datetime.datetime.now())},
    # )
    
    cache_key = f"search:{query}:{limit}:{offset}"
    cached_results = await redis_client.get(cache_key)
    if cached_results:
        return json.loads(cached_results)
    
    product_service = ProductService(db)
    results = product_service.search(query, limit, offset)
    
    # Store result in Redis (expires in 1 hour 3600 secs 1 min 60 sec)
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
    user = user_authorization(token, db)
    
    # ✅ Validate product ownership
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id, user)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this product")

    # Delete product images in product service
    # Delete product from database
    product_service.delete_product(product_id, user)

    return {"message": "Product deleted successfully"}

    
@router.post("/create", response_model=ProductDTO)
async def create_product(
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    is_dollar: bool = Form(False),
    activated: bool = Form(True),
    category: str = Form(...),
    images: List[UploadFile] = File(None),  # Accept multiple images
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    Create a new product. Only authenticated users can add a product.
    """
    user = user_authorization(token, db)

    product_service = ProductService(db)

    product_data = ProductCreateDTO(
        name=name, 
        description=description, 
        price=price, 
        category=category,
        is_dollar=is_dollar,
        activated=activated,
    )
     # Create product
    new_product = product_service.create_product(user.email, product_data)
    
    img_service = ImageService()
    if images and len(images) > 0:
        image_urls = [await img_service.process_and_store_image(image) for image in images] # Process and store images
        product_service.add_images_to_product(new_product.id, image_urls) # Associate images with product
    else:
        default_img = os.path.abspath("app/web/static/icons/no_image.webp")
        image_urls = [await img_service.process_and_store_image(default_img)]
        product_service.add_images_to_product(new_product.id, image_urls)
        
    return new_product


@router.get("/mylist", response_model=List[ProductDTO])
def get_products_my_list(token: str = Depends(token_scheme), db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    """
    Get a list of products, sorted by latest first.
    """
    user = user_authorization(token, db) 
    product_service = ProductService(db)
    return product_service.get_user_products(user.id, limit, offset)


@router.get("/list", response_model=List[ProductDTO])
def get_products_list(db: Session = Depends(get_db), limit: int = 100, offset: int = 0):
    """
    Get a list of recent products.
    """
    product_service = ProductService(db)
    return product_service.get_all_products(limit, offset)


@router.put("/update/{product_id}", response_model=ProductDTO)
async def update_product(
        product_id: int,
        name: str = Form(None),
        description: str = Form(None),
        price: float = Form(None),
        is_dollar: bool = Form(False),
        activated: bool = Form(True),
        category: str = Form(None),
        images: List[UploadFile] = File(None),  # Optional images
        keep_existing_images: bool = Form(True),
        token: str = Depends(token_scheme),
        db: Session = Depends(get_db)
    ):
    """
    Update an existing product. Only the product owner can update it.
    """
    
    user = user_authorization(token, db)

    product_service = ProductService(db)
    
    product = product_service.get_product_by_id(product_id, user)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this product")

    updated_data = {
        "name": name or product.name,
        "description": description or product.description,
        "price": price if price is not None else product.price,
        "category": category or product.category,
        "is_dollar": is_dollar,
        "activated": activated,
    }

    if images:
        image_service = ImageService()
        new_image_urls = [await image_service.process_and_store_image(image) for image in images[:10]]
        product_service.update_product_images(product_id, new_image_urls, keep_existing_images)
    
    if not activated:
        fav_service = FavService(db)
        fav_service.remove_from_favs(product_id)
    
    updated_product = product_service.update_product(product_id, user, updated_data)

    return updated_product


@router.get("/{product_id}", response_model=ProductDTO)
def get_product(product_id: int, request: Request, db: Session = Depends(get_db), ):
    """Fetch product details by ID."""
    
    token = request.headers.get("Authorization").replace("Bearer ", "")
    product_service = ProductService(db)
    user = None
    if token != 'null':
        try:
            user = user_authorization(token, db)
        except Exception as e:
            logger.info(f"Trying get product detail with invalid token, Error: {e}")
            user = None
            
    product = product_service.get_product_by_id(product_id, user)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_dto = ProductDTO.model_validate(product)
    product_dto.image_urls = [img.image_url for img in product.images]
    
    return product_dto

@router.post("/my/{product_id}", response_model=ProductDTO)
def get_product(product_id: int, db: Session = Depends(get_db), token: str = Depends(token_scheme),):
    """Fetch product details by ID."""
    
    user = user_authorization(token, db)
    
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id, user)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product_dto = ProductDTO.model_validate(product)
    product_dto.image_urls = [img.image_url for img in product.images]
    
    return product_dto
