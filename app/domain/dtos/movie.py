from pydantic import BaseModel
from fastapi import File, Form, UploadFile
from typing import Optional


class MovieDTO(BaseModel):
    id: int
    title: str
    description: str | None
    file_path: str
    is_public: bool

    class Config:
        from_attributes = True



class UpdateMovieRequest:
    def __init__(
        self,
        title: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        is_public: Optional[bool] = Form(None),
        thumbnail_path: Optional[UploadFile] = File(None)
    ):
        self.title = title
        self.description = description
        self.is_public = is_public
        self.thumbnail_path = thumbnail_path