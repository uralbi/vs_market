from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from app.utils.context import global_context
import os

router = APIRouter(    
    prefix='',
    tags=['Websites'])


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "../templates"))

@router.get("/")
def product_list_page(request: Request, context: dict = Depends(global_context)):
    """ Serve the product listing page """
    return templates.TemplateResponse("index.html", {**context, "title": "iMarket"})

@router.get("/update-product/{product_id}")
def update_product_page(request: Request, product_id: int):
    """ Update product page """
    return templates.TemplateResponse("update_product.html", {"request": request, "product_id": product_id})

@router.get("/create-product")
def create_product_page(request: Request):
    """ Create product page """
    return templates.TemplateResponse("create_product.html", {"request": request, "title": "Create Product"})