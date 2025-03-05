from pydantic import BaseModel, EmailStr, Field, field_validator
import phonenumbers


class UserRegistrationDTO(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLoginDTO(BaseModel):
    email: EmailStr
    password: str


class UserRoleDTO(BaseModel):
    user_id: int
    user_role: str
    
    
class ChangePasswordDTO(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)


class UpdateUsernameDTO(BaseModel):
    username: str
    password: str
    
class UpdateEmailDTO(BaseModel):
    new_email: EmailStr
    password: str = Field(..., min_length=6)
