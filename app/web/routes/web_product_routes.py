from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import os

router = APIRouter(    
    prefix='',
    tags=['Websites'])


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "../templates"))

@router.get("/")
def product_list_page(request: Request):
    """ Serve the product listing page """
    return templates.TemplateResponse("index.html", {"request": request, "title": "iMarket"})

@router.get("/create-product")
def create_product_page(request: Request):
    """ Serve the product creation page """
    return templates.TemplateResponse("create_product.html", {"request": request, "title": "Create Product"})