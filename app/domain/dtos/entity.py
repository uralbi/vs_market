from pydantic import BaseModel, EmailStr, Field, field_validator
import phonenumbers


class EntityUpdateDTO(BaseModel):
    """ DTO for updating an entity (partial update) """
    entity_name: str | None = None
    entity_phone: str | None = None
    entity_address: str | None = None
    entity_whatsapp: str | None = None


class EntityCreateDTO(BaseModel):
    entity_name: str
    entity_phone: str = Field(..., description="Phone number in international format")
    entity_address: str
    entity_whatsapp: str = Field(..., description="WhatsApp number in international format")

    # @field_validator("entity_phone", "entity_whatsapp")
    # @classmethod
    # def validate_phone(cls, value: str) -> str:
    #     try:
    #         phone_number = phonenumbers.parse(value, None)  # Auto-detect country
    #         if not phonenumbers.is_valid_number(phone_number):
    #             raise ValueError("Invalid phone number format")
    #         return phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
    #     except Exception:
    #         raise ValueError("Invalid phone number")