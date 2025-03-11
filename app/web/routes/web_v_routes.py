from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.utils.context import global_context
from app.services.chat_service import ChatService
from app.services.product_service import ProductService
from app.core.template_config import templates
import os

router = APIRouter(    
    prefix='/movies',
    tags=['Videos'])

@router.get("/update")
def stream_movie_page(request: Request, context: dict = Depends(global_context)):
    """ Movie Search page """
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("movie_forms/update.html", {**context, "title": "Aiber Update"})

@router.get("/search")
def stream_movie_page(request: Request, context: dict = Depends(global_context)):
    """ Movie Search page """

    return templates.TemplateResponse("movie_forms/search.html", {**context, "title": "Aiber Search"})

@router.get("/preview")
def stream_movie_page(request: Request, context: dict = Depends(global_context)):
    """ Movie View page """

    return templates.TemplateResponse("movie_forms/preview.html", {**context, "title": "Aiber Preview"})

@router.get("/stream")
def stream_movie_page(request: Request, context: dict = Depends(global_context)):
    """ Movie View page """

    return templates.TemplateResponse("movie_forms/stream.html", {**context, "title": "Aiber Stream"})

@router.get("/upload")
def upload_page(request: Request, context: dict = Depends(global_context)):
    """ Movie Upload page """
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("movie_forms/upload.html", {**context, "title": "Aiber Post"})