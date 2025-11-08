from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List

class Product(BaseModel):

    id: str
    name: str
    description: str
    price: float
    is_dollar: bool
    category: str
    created_at: datetime
    owner_id: str
    images: List[str] = []

    model_config = ConfigDict(from_attributes=True)
    