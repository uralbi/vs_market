from fastapi import APIRouter, Depends, Query, HTTPException, Security, Response, Body
from app.services.user_service import UserService
from app.infra.database.db import get_db
from app.domain.dtos.user import UserRegistrationDTO, UserLoginDTO, ChangePasswordDTO, UpdateEmailDTO
from app.infra.database.models import UserRole
from sqlalchemy.orm import Session
from app.domain.security.auth_token import decode_access_token, create_access_token, \
    create_refresh_token, verify_refresh_token
from fastapi.security import OAuth2PasswordBearer
from app.services.product_service import ProductService
from app.domain.security.auth_user import user_authorization, user_admin_auth
from pydantic import BaseModel
from typing import Optional

router = APIRouter(
    prefix='/api/auth',
    tags=['Authorizatioin']
)

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.post("/deactivate")
def deactivate(token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Logs out the user by clearing the authentication token from cookies.
    """

    user = user_authorization(token, db)
    user_service = UserService(db)
    user_service.deactivate_user(user.id)
    product_service = ProductService(db)
    product_service.deactivate_user_products(user.id)
    return {"message": "Your account is deactivated, and will be deleted in 30 days!."}


class UserIDRequest(BaseModel):
    user_id: int
    
@router.post("/deactivate_user")
def deactivate_user(payload: UserIDRequest, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """
    Logs out the user by clearing the authentication token from cookies.
    """
    print("the user id: ", payload.user_id)
    user_id = payload.user_id
    user = user_authorization(token, db)
    
    if user.role != "ADMIN":
        return HTTPException(status_code=401, detail="Unauthorized")
    user_service = UserService(db)
    user_service.deactivate_user(user_id)
    product_service = ProductService(db)
    product_service.deactivate_user_products(user_id)
    return {"message": "Your account is deactivated"}

@router.put("/change-password")
def change_password(
    password_data: ChangePasswordDTO,
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    API Endpoint: Allows authenticated users to change their password.
    """

    user = user_authorization(token, db)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.verify_password(password_data.old_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    if user.verify_password(password_data.new_password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old password")
    user_service = UserService(db)
    user_service.update_password(user, password_data.new_password)
    return {"message": "Password changed successfully"}


@router.put("/update-email")
def update_email(
    email_data: UpdateEmailDTO,
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    API Endpoint: Allows authenticated users to update their email.
    """
    user = user_authorization(token, db)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.verify_password(email_data.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    if email_data.new_email == user.email:
        raise HTTPException(status_code=400, detail="Email already in use")

    user_service = UserService(db)
    user_service.update_email(user, email_data.new_email)
    return {"message": "Email updated successfully"}


@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db)):
    """
    Logs out the user by clearing the authentication token from cookies.
    """
    response.delete_cookie("access_token")  # Remove token from cookies
    response.delete_cookie("refresh_token", httponly=True, secure=True, samesite="Strict")
    return {"message": "Logged out"}


@router.get("/users")
async def get_all_user(
    limit: int, offset: int, 
    email: Optional[str] = Query(None, description="Search by email (substring match)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    token: str = Security(token_scheme), 
    db: Session = Depends(get_db)):
    
    user = user_authorization(token, db)

    if not user or user.role != 'ADMIN':
        raise HTTPException(status_code=404, detail="User not found")  
    user_service = UserService(db)
    users = user_service.get_all_users(limit, offset, email, is_active)
    return users


@router.get("/me")
async def read_current_user(token: str = Security(token_scheme), db: Session = Depends(get_db)):
    user = user_authorization(token, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "email": user.email, "is_active": user.is_active, "user_id": user.id}


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):

    refresh_token = payload.refresh_token
    payload = verify_refresh_token(refresh_token)  # Validate refresh token
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_email = payload["sub"]
    user_service = UserService(db)
    stored_user = user_service.get_user_by_email(user_email)
    
    if not stored_user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token({"sub": stored_user.email})
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/token")
async def login(user: UserLoginDTO, db: Session = Depends(get_db)):
    user_service = UserService(db)
    stored_user = user_service.get_user_by_email(user.email) 

    if not stored_user or not stored_user.verify_password(user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not stored_user.is_active:
        # user_service.send_activation_email(stored_user.email)
        raise HTTPException(status_code=400, detail="Account not activated. Please contact the web manager.")

    access_token = create_access_token({"sub": stored_user.email})
    refresh_token = create_refresh_token({"sub": stored_user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register")
def register(user_data: UserRegistrationDTO, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.register_user(user_data)


@router.get("/verify-email")
async def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.is_active:
        return {"msg": "Email already verified."}
    
    user.is_active = True
    db.commit()
    
    return {"msg": "Email verified. Your account is now activated."}


@router.get("/activate_user")
async def activate_user(user_id: int, token: str = Security(token_scheme), db: Session = Depends(get_db)):
    user = user_authorization(token, db)
    if not user or user.role != "ADMIN":
        raise HTTPException(status_code=401, detail="Unauthorized")
    user_service = UserService(db)
    act_user = user_service.activate_user(user_id)
    return {"message": f"User [ {act_user.id} {act_user.email} ] is activated"}


class RoleDataRequest(BaseModel):
    user_id: int
    user_role: str
    
@router.put("/update-role")
def update_email(
    data: RoleDataRequest, token: str = Depends(token_scheme), db: Session = Depends(get_db)
        ):
    """
    API Endpoint: Allows authenticated users to update their email.
    """
    user = user_authorization(token, db)
    if not user_admin_auth(user):
        HTTPException(status_code=401, detail="Unauthorized")
    
    user_service = UserService(db)
    user_id = data.user_id
    new_role = UserRole(data.user_role)
    return user_service.update_user_role(user_id, new_role)
    