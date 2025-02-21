from pydantic import BaseModel


class MovieDTO(BaseModel):
    id: int
    title: str
    description: str | None
    file_path: str
    is_public: bool

    class Config:
        orm_mode = True