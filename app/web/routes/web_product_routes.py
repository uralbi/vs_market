from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.infra.database.db import get_db
from app.utils.context import global_context
from app.services.chat_service import ChatService
from app.services.product_service import ProductService
from app.core.template_config import templates
from app.infra.database.models import ProductModel
import os
from dotenv import load_dotenv

DOMAIN = os.getenv("DOMAIN")

router = APIRouter(    
    prefix='',
    tags=['Websites'])


@router.get("/robots.txt", response_class=Response)
async def serve_robots_txt():
    """
    Serve robots.txt for SEO optimization.
    """
    robots_txt_content = f"""User-agent: *
        Disallow: /admin/
        Disallow: /api/
        Disallow: /cart/
        Disallow: /checkout/
        Disallow: /account/
        Disallow: /login/
        Disallow: /register/
        Disallow: /profile/
        Disallow: /messages/
        Disallow: /favorites/
        Disallow: /notifications/
        Disallow: /password-reset/
        Disallow: /settings/

        Allow: /products/
        Allow: /categories/
        Allow: /search/
        Allow: /static/images/
        Allow: /static/css/
        Allow: /static/js/

        Sitemap: {DOMAIN}/sitemap.xml
        """

    return Response(content=robots_txt_content, media_type="text/plain")

@router.get("/sitemap.xml", response_class=Response, response_model=None)
async def generate_sitemap(db=Depends(get_db)):
    """
    Dynamically generates sitemap.xml with product and category URLs using pagination.
    """

    base_url = DOMAIN
    sitemap_urls = [
        f"<url><loc>{base_url}/</loc></url>",
        f"<url><loc>{base_url}/contacts</loc></url>",
    ]
    prod_service = ProductService(db)
    limit = 1000
    offset = 0
    while True:
        products = prod_service.get_all_products(limit, offset)
        if not products:
            break  # Stop fetching if no more products
        product_urls = [f"<url><loc>{base_url}/product/{p.id}</loc></url>" for p in products]
        sitemap_urls.extend(product_urls)
        offset += limit
        
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            {''.join(sitemap_urls)}
        </urlset>
        """

    return Response(content=sitemap_content, media_type="application/xml")


@router.get("/product/{product_id}")
def get_product_page(request: Request, product_id: int, context: dict = Depends(global_context)):
    """ Product Detail page """

    return templates.TemplateResponse("product_forms/detail.html", {**context, "product_id": product_id,"title": "Aiber Item"})

@router.get("/messages")
def message_page(request: Request, context: dict = Depends(global_context), db: Session = Depends(get_db)):
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    room_id = request.query_params.get("room_id")
    user_id = context['current_user'].id
    chat_service = ChatService(db)
    other_id = chat_service.get_other_user_id(room_id, user_id)
    
    return templates.TemplateResponse("chat.html", {**context, "other_id": other_id, "title": "Aiber Chat"})

@router.get("/messages/users")
def message_page(request: Request, context: dict = Depends(global_context), db: Session = Depends(get_db)):
    """ Serve the Chat Page """
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
    return templates.TemplateResponse("chat.html", {**context, "other_id": receiver_id, "room_id": room.id, 'product': subject, "title": "Aiber Chat"})


@router.get("/")
def product_list_page(request: Request, context: dict = Depends(global_context)):
    """ Serve the product listing page """
    return templates.TemplateResponse("index.html", {**context, "title": "Aiber Объявления для всех"})

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
    return templates.TemplateResponse("product_forms/create.html", {**context, "title": "Aiber Post"})