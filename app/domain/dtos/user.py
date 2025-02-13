from pydantic import BaseModel, EmailStr, Field, field_validator
import phonenumbers


class UserRegistrationDTO(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str
    

class ChangePasswordDTO(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)

class UpdateEmailDTO(BaseModel):
    new_email: EmailStr
    password: str = Field(..., min_length=6)
