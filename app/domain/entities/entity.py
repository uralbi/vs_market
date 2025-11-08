from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Entity(BaseModel):

    id: str
    creator_id: str
    entity_name: str
    entity_phone: str
    entity_address: str
    entity_whatsapp: str
    created_at: datetime
    
    class Config:
        from_attributes = True