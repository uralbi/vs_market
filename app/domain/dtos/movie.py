from pydantic import BaseModel


class MovieDTO(BaseModel):
    id: int
    title: str
    description: str | None
    file_path: str
    is_public: bool

    class Config:
        from_attributes = True


class UpdateMovieRequest(BaseModel):
    title: str | None
    description: str | None
    is_public: bool