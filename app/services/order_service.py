from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.infra.repositories.movie_repository import MovieRepository
from app.infra.database.models import MovieModel, OrderModel
import os, shutil

class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def check_is_ordered(self, movie_id: int):
        order = self.db.query(OrderModel).filter(
            OrderModel.movie_id == movie_id,
            OrderModel.status.in_(["PENDING", "COMPLETED"])
        ).first()
        return order is not None
            
    def check_order_status(self, user_id: int, movie_id: int):
        order = self.db.query(OrderModel).filter(
        OrderModel.user_id == user_id, 
        OrderModel.movie_id == movie_id, 
        ).first()

        if not order:
            raise HTTPException(status_code=403, detail="Вы не купили данный фильм")
        if order.status == "PENDING" or order.status=="FAILED":
            raise HTTPException(status_code=403, detail="Вы не завершили покупку фильма")
        
        return True
    
    def get_user_orders(self, user_id: int):
        orders = self.db.query(OrderModel).filter(
                        OrderModel.user_id == user_id).all()
        return orders