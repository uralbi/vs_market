from pydantic import BaseModel
from fastapi import File, Form, UploadFile
from typing import Optional


class MovieDTO(BaseModel):
    id: str
    title: str
    description: str
    price: int
    file_path: str
    is_public: bool
    file: UploadFile
    
    class Config:
        from_attributes = True


class UpdateMovieRequest:
    def __init__(
        self,
        title: Optional[str] = Form(None),
        description: Optional[str] = Form(None),
        price: Optional[int] = Form(None),
        is_public: Optional[bool] = Form(None),
        thumbnail_path: Optional[UploadFile] = File(None)
    ):
        self.title = title
        self.description = description
        self.is_public = is_public
        self.price = price
        self.thumbnail_path = thumbnail_path