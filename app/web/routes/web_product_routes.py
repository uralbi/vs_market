from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.utils.context import global_context
import os

router = APIRouter(    
    prefix='',
    tags=['Websites'])


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "../templates"))


@router.get("/product/{product_id}")
def get_product_page(request: Request, product_id: int, context: dict = Depends(global_context)):
    """ Product Detail page """

    return templates.TemplateResponse("product_detail.html", {**context, "product_id": product_id,})

@router.get("/messages")
def message_page(request: Request, context: dict = Depends(global_context)):
    """ Serve the product listing page """
    
    receiver_id = request.query_params.get("receiver_id")
    user_id = request.query_params.get("user_id")
    
    if user_id == receiver_id or not user_id:
        prev_page = request.query_params.get("prev_page", "/")
        return RedirectResponse(url=prev_page)
    
    return templates.TemplateResponse("chat.html", {**context, "title": "Messages"})

@router.get("/")
def product_list_page(request: Request, context: dict = Depends(global_context)):
    """ Serve the product listing page """
    return templates.TemplateResponse("index.html", {**context, "title": "iMarket"})

@router.get("/update-product/{product_id}")
def update_product_page(request: Request, product_id: int, context: dict = Depends(global_context)):
    """ Update product page """
    return templates.TemplateResponse("update_product.html", {**context, "product_id": product_id})

@router.get("/create-product")
def create_product_page(request: Request, context: dict = Depends(global_context)):
    """ Create product page """
    return templates.TemplateResponse("create_product.html", {**context, "title": "Create Product"})