from pydantic import BaseModel, EmailStr, Field, field_validator
from app.utils.phone_val import validate_phone


class EntityUpdateDTO(BaseModel):
    """ DTO for updating an entity (partial update) """
    entity_name: str | None = None
    entity_phone: str | None = None
    entity_address: str | None = None
    entity_whatsapp: str | None = None
    
    @field_validator("entity_phone", "entity_whatsapp")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone(value)


class EntityCreateDTO(BaseModel):
    entity_name: str
    entity_phone: str = Field(..., description="Phone number in international format")
    entity_address: str
    entity_whatsapp: str = Field(..., description="WhatsApp number in international format")

    @field_validator("entity_phone", "entity_whatsapp")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return validate_phone(value)