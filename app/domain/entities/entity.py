from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Entity(BaseModel):

    id: int
    creator_id: int
    entity_name: str
    entity_phone: str
    entity_address: str
    entity_whatsapp: str
    created_at: datetime
    
    class Config:
        from_attributes = True