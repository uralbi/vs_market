from sqlalchemy.orm import Session
from app.infra.database.models import EntityModel
from app.domain.entities.entity import Entity


class EntityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_entity(self, entity: Entity) -> Entity:
        """
        Save entity to the database.
        """
        db_entity = EntityModel(
            creator_id=entity.creator_id,
            entity_name=entity.entity_name,
            entity_phone=entity.entity_phone,
            entity_address=entity.entity_address,
            entity_whatsapp=entity.entity_whatsapp,
            created_at=entity.created_at
        )

        self.db.add(db_entity)
        self.db.commit()
        self.db.refresh(db_entity)

        return db_entity

    def get_entity_by_id(self, entity_id: int):
        """
        Fetch an entity by ID.
        """
        return self.db.query(EntityModel).filter(EntityModel.id == entity_id).first()
    
    def get_entity_by_user(self, user_id: int):
        """"
        Fetch an entity by user ID
        """
        return self.db.query(EntityModel).filter(EntityModel.creator_id == user_id).first()
    
    def delete_entity(self, entity):
        """
        Delete the given entity.
        """
        self.db.delete(entity)
        self.db.commit()