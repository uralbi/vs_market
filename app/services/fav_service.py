from sqlalchemy.orm import Session

from app.infra.database.models import favorites_table
from app.domain.entities.user import User


class FavService:
    def __init__(self, db: Session):
        self.db = db
    
    def remove_from_favs(self, product_id: str):
        """ Remove product from all favorites. Returns 0 if no products """
        return self.db.query(favorites_table).filter(favorites_table.c.product_id == product_id).delete()