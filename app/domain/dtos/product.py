from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from app.domain.dtos.entity import EntityCreateDTO
from datetime import datetime


class ProductCreateDTO(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., max_length=10000)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=2, max_length=100)
    image_urls: List[str] = Field(default=[], max_length=10)  # Max 20 images
    is_dollar: bool = Field(default=False)
    activated: bool = Field(default=True)
    
    
class ProductDTO(ProductCreateDTO):
    id: str
    created_at: datetime
    owner_id: str

    class Config:
        from_attributes = True


class ProductImageDTO(BaseModel):
    id: str
    product_id: str
    image_url: HttpUrl

    class Config:
        from_attributes = True
