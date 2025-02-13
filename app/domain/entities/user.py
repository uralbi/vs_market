from datetime import datetime
from pydantic import BaseModel


class User(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool = False
    created_at: datetime

