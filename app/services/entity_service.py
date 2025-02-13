from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.domain.dtos.entity import EntityCreateDTO, EntityUpdateDTO
from app.infra.repositories.entity_repository import EntityRepository
from app.infra.database.models import EntityModel
from app.domain.entities.user import User


class EntityService:
    def __init__(self, db: Session):
        self.db = db
        self.entity_repo = EntityRepository(db)

    def create_entity(self, user, entity_data: EntityCreateDTO) -> EntityModel:
        """
        Create a new entity. Only active users can create an entity.
        """
        if not user or not user.is_active:
            raise HTTPException(status_code=403, detail="Only active users can create an entity")

        entity = EntityModel(
            creator_id=user.id,
            entity_name=entity_data.entity_name,
            entity_phone=entity_data.entity_phone,
            entity_address=entity_data.entity_address,
            entity_whatsapp=entity_data.entity_whatsapp,
            created_at=datetime.now()
        )

        return self.entity_repo.create_entity(entity)

    def update_entity(self, entity: EntityModel, entity_data: EntityUpdateDTO):
        """ Update entity fields if provided """
        for key, value in entity_data.model_dump(exclude_none=True).items():
            setattr(entity, key, value)  # Dynamically update fields

        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def get_entity_by_user(self, user) -> User:
        return self.entity_repo.get_entity_by_user(user.id)
        
    def delete_entity(self, user, entity_id: int) -> dict:
        """ Delete an entity. Only the entity owner can delete it. """
        
        entity = self.entity_repo.get_entity_by_id(entity_id)

        if not entity:
            raise HTTPException(status_code=404, detail="Entity not found")

        if entity.creator_id != user.id:
            raise HTTPException(status_code=403, detail="You can only delete your own entity")

        self.entity_repo.delete_entity(entity)
        return {"message": "Entity deleted successfully"}