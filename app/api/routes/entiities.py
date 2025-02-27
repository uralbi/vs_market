from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from fastapi.openapi.models import APIKey
from app.infra.database.db import get_db
from app.services.user_service import UserService
from app.services.entity_service import EntityService
from app.domain.dtos.entity import EntityCreateDTO, EntityUpdateDTO
from app.domain.entities.entity import Entity
from app.domain.security.auth_token import decode_access_token
from app.domain.security.auth_user import user_authorization


router = APIRouter(    
    prefix='/api/ent',
    tags=['Entities / Profiles']
)
token_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


@router.put("/update", response_model=dict)
def update_entity(
    entity_data: EntityUpdateDTO,
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    API Endpoint: Update entity details (only specific fields can be changed)
    """
   
    user = user_authorization(token, db)

    entity_service = EntityService(db)
    entity = entity_service.get_entity_by_user_id(user.id)

    if not entity:
        raise HTTPException(status_code=404, detail="No entity found")
    entity_service.update_entity(entity, entity_data)
    
    return {"message": "Entity updated successfully", "updated_fields": entity_data.model_dump(exclude_none=True)}


@router.post("/", response_model=Entity)
def create_entity(
    entity_data: EntityCreateDTO,
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    API Endpoint: Create a new entity. Only active users can create an entity.
    """
    user = user_authorization(token, db)

    entity_service = EntityService(db)
    entity_model = entity_service.create_entity(user, entity_data)

    return Entity.model_validate(entity_model)


@router.get("/{user_id}", response_model=Entity)
def get_user_entity(user_id: int, db: Session = Depends(get_db)):
    """Fetch the entity of the currently logged-in user."""
    
    entity_service = EntityService(db)
    entity = entity_service.get_entity_by_user_id(user_id)

    if not entity:
        raise HTTPException(status_code=404, detail="No entity found")

    return entity

@router.delete("/{entity_id}")
def delete_entity(
    entity_id: int,
    token: str = Depends(token_scheme),
    db: Session = Depends(get_db)
):
    """
    API Endpoint: Delete an entity. Only the owner can delete their entity.
    """
    user = user_authorization(token, db)
    entity_service = EntityService(db)
    
    return entity_service.delete_entity(user, entity_id)