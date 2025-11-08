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
    user_id: str
    user_role: str
    
    
class ChangePasswordDTO(BaseModel):
    old_password: str = Field(..., min_length=6)
    new_password: str = Field(..., min_length=6)
    
    @field_validator("old_password", "new_password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 6:
            raise ValueError("Пароль должен быть не менее 6 символов")
        return value


class UpdateUsernameDTO(BaseModel):
    username: str
    password: str
    
class UpdateEmailDTO(BaseModel):
    new_email: EmailStr
    password: str = Field(..., min_length=6)
