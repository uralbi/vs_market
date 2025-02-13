from pydantic import BaseModel, EmailStr, Field, field_validator
import phonenumbers


class UserRegistrationDTO(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str
    
