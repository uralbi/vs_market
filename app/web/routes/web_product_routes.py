from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.utils.context import global_context
from app.services.chat_service import ChatService
from app.services.product_service import ProductService
from app.core.template_config import templates


router = APIRouter(    
    prefix='',
    tags=['Websites'])

    
@router.get("/product/{product_id}")
def get_product_page(request: Request, product_id: int, context: dict = Depends(global_context)):
    """ Product Detail page """

    return templates.TemplateResponse("product_forms/detail.html", {**context, "product_id": product_id,})

@router.get("/messages")
def message_page(request: Request, context: dict = Depends(global_context), db: Session = Depends(get_db)):
    """ Serve the product listing page """
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    room_id = request.query_params.get("room_id")
    user_id = context['current_user'].id
    chat_service = ChatService(db)
    other_id = chat_service.get_other_user_id(room_id, user_id)
    
    return templates.TemplateResponse("chat.html", {**context, "other_id": other_id})

@router.get("/messages/users")
def message_page(request: Request, context: dict = Depends(global_context), db: Session = Depends(get_db)):
    """ Serve the product listing page """
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    user_id = request.query_params.get("user_id")
    receiver_id = request.query_params.get("receiver_id")
    
    if user_id == receiver_id:
        return
    
    product_id = request.query_params.get("product_id")
    subject = product_id
    if product_id.isdigit(): 
        product_service = ProductService(db)
        prod = product_service.get_product_by_id(product_id, None)
        subject = prod.name
    chat_service = ChatService(db)
    room = chat_service.get_or_create_chat_room(user_id, receiver_id, subject)
    return templates.TemplateResponse("chat.html", {**context, "other_id": receiver_id, "room_id": room.id, 'product': subject })


@router.get("/")
def product_list_page(request: Request, context: dict = Depends(global_context)):
    """ Serve the product listing page """
    return templates.TemplateResponse("index.html", {**context, "title": "iMarket"})

@router.get("/update-product/{product_id}")
def update_product_page(request: Request, product_id: int, context: dict = Depends(global_context)):
    """ Update product page """
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("product_forms/update.html", {**context, "product_id": product_id})

@router.get("/create-product")
def create_product_page(request: Request, context: dict = Depends(global_context)):
    """ Create product page """
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("product_forms/create.html", {**context, "title": "Create Product"})