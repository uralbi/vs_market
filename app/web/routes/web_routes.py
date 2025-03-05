from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from app.utils.context import global_context
from app.core.template_config import templates
import os


router = APIRouter(    
    prefix='',
    tags=['Websites'])

@router.get("/settings", name="settings_page")
def settings_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Admin page"""
    return templates.TemplateResponse("auth/settings.html", {**context, "title": "iSettings"})

@router.get("/admin", name="admin_page")
def admin_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Admin page"""
    return templates.TemplateResponse("auth/admin.html", {**context, "title": "iAdmin"})

@router.get("/login", name="login_page")
def about_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Login page"""
    return templates.TemplateResponse("auth/login.html", {**context, "title": "iMarket"})

@router.get("/about")
def contact_page(request: Request, context: dict = Depends(global_context)):
    """Serve the About page"""
    return templates.TemplateResponse("auth/about.html", {**context, "title": "iMarket"})

@router.get("/register", name="register_page")
def register_page(request: Request, context: dict = Depends(global_context)):
    """Serves the registration page."""
    return templates.TemplateResponse("auth/register.html", {**context, "title": "iMarket"})