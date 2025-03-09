from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.utils.context import global_context
from app.core.template_config import templates
import os


router = APIRouter(    
    prefix='',
    tags=['Websites'])

@router.get("/admin", name="admin_page")
def admin_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Admin page"""
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("auth/admin.html", {**context, "title": "iAdmin"})

@router.get("/login", name="login_page")
def about_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Login page"""
    return templates.TemplateResponse("auth/login.html", {**context, "title": "iMarket"})

@router.get("/about")
def contact_page(request: Request, context: dict = Depends(global_context)):
    """Serve the About page"""
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse("auth/about.html", {**context, "title": "iMarket"})

@router.get("/register", name="register_page")
def register_page(request: Request, context: dict = Depends(global_context)):
    """Serves the registration page."""
    return templates.TemplateResponse("auth/register.html", {**context, "title": "iMarket"})