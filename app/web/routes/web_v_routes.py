from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.utils.context import global_context
from app.services.chat_service import ChatService
from app.services.product_service import ProductService
import os

router = APIRouter(    
    prefix='/movies',
    tags=['Videos'])


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "../templates"))



@router.get("/stream")
def stream_movie_page(request: Request, context: dict = Depends(global_context)):
    """ Movie Upload page """

    return templates.TemplateResponse("mov_stream.html", {**context, })

@router.get("/upload")
def upload_page(request: Request, context: dict = Depends(global_context)):
    """ Movie Upload page """

    return templates.TemplateResponse("mov_upload.html", {**context, })