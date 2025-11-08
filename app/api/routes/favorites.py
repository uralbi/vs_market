from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.infra.database.models import UserModel, ProductModel
from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.domain.security.auth_token import decode_access_token
from app.domain.security.auth_user import user_authorization
from fastapi.security import OAuth2PasswordBearer


router = APIRouter(
    prefix="/favs",
    tags=["Favorites"]
)

token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.get("/")
def get_favorite_products(token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """Get the list of favorite products for the authenticated user"""

    user = user_authorization(token, db)
    user_service = UserService(db)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user_service.get_favorites(user.id)  # Returns the list of favorite products


@router.post("/{product_id}")
def add_to_favorites(product_id: str, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """Allow a user to add a product to their favorites"""
    
    user = user_authorization(token, db)
    
    user_service = UserService(db)
    product_service = ProductService(db)
    
    product = product_service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Не найдено")
    if product.owner_id == user.id:
        raise HTTPException(status_code=400, detail="Это ваше объявление!")

    if product in user.favorite_products:
        user_service.remove_from_favorites(product, user)
        return {"message": "Объявление удалено из Избранных"}
    user_service.add_to_favorites(product, user)
    return {"message": "Объвление добавлено в Избранное"}


@router.delete("/{product_id}")
def remove_from_favorites(product_id: str, token: str = Depends(token_scheme), db: Session = Depends(get_db)):
    """Allow a user to remove a product from their favorites"""
    user = user_authorization(token, db)
    
    product_service = ProductService(db)
    product = product_service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Объявление не найдено")
    if product not in user.favorite_products:
        raise HTTPException(status_code=400, detail="Объявления нет в Избранных")

    user.favorite_products.remove(product)
    db.commit()

    return {"message": "Объявление удалено с Избранных"}

