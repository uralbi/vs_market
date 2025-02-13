from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List

class Product(BaseModel):

    id: int
    
    name: str
    description: str
    price: float
    category: str
    created_at: datetime
    owner_id: int
    images: List[str] = []

    model_config = ConfigDict(from_attributes=True)
    