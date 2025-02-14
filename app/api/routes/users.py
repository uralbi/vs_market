from fastapi import APIRouter, Depends, Query, HTTPException, Security, Response
from app.services.user_service import UserService
from app.infra.database.db import get_db
from app.domain.dtos.user import UserRegistrationDTO, UserLoginDTO, ChangePasswordDTO, UpdateEmailDTO
from sqlalchemy.orm import Session
from app.domain.security.auth_token import decode_access_token, create_access_token
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.models import APIKey

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
    payload = decode_access_token(token)
    email = payload.get("sub")
    user_service = UserService(db)
    user_service.deactivate_user(email)
    return {"message": "Your account is deactivated, and will be deleted in 30 days!."}

@router.put("/change-password")
def change_password(
    password_data: ChangePasswordDTO,
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    API Endpoint: Allows authenticated users to change their password.
    """
    payload = decode_access_token(token)
    email = payload.get("sub")

    user_service = UserService(db)
    user = user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.verify_password(password_data.old_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    if user.verify_password(password_data.new_password):
        raise HTTPException(status_code=400, detail="New password cannot be the same as the old password")

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
    payload = decode_access_token(token)
    email = payload.get("sub")

    user_service = UserService(db)
    user = user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.verify_password(email_data.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    if user_service.get_user_by_email(email_data.new_email):
        raise HTTPException(status_code=400, detail="Email already in use")

    user_service.update_email(user, email_data.new_email)
    return {"message": "Email updated successfully"}


@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db)):
    """
    Logs out the user by clearing the authentication token from cookies.
    """
    response.delete_cookie("access_token")  # Remove token from cookies
    return {"message": "Successfully logged out"}


@router.get("/me")
async def read_current_user(token: str = Security(token_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    email = payload.get("sub")
    user_service = UserService(db)
    user = user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "email": user.email, "is_active": user.is_active}


@router.post("/token")
async def login(user: UserLoginDTO, db: Session = Depends(get_db)):
    user_service = UserService(db)
    stored_user = user_service.get_user_by_email(user.email) # returns User / User.verify_password()
    print('stored user', stored_user.email, stored_user.is_active)
    if not stored_user or not stored_user.verify_password(user.password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    if not stored_user.is_active:
        user_service.send_activation_email(stored_user.email)
        raise HTTPException(status_code=400, detail="Account not activated. Please verify your email.")
    
    access_token = create_access_token({"sub": stored_user.email})
    return {"access_token": access_token, "token_type": "bearer"}


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