from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.infra.database.models import OrderModel


class PaymentService:
    def __init__(self, order:OrderModel, db: Session):
        self.order = order
        self.db = db

    def payment_success (self):
        self.order.status = "completed"
        self.db.commit()
        return True
    
    def payment_failed(self):
        self.order.status = "failed"
        self.db.commit()
        return False