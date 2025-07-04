from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.utils.context import global_context
from app.core.template_config import templates
from app.services.user_service import UserService
from app.domain.security.auth_token import decode_access_token
from app.domain.security.pass_gen import generate_password
from app.infra.tasks.email_tasks import send_notification_email
from app.infra.database.db import get_db
from sqlalchemy.orm import Session
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
    return templates.TemplateResponse("auth/admin.html", {**context, "title": "Aiber Admin"})

@router.get("/password-change-form", name="pass_request_page")
def pass_request_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Admin page"""
    return templates.TemplateResponse("auth/pass_request.html", {**context, "title": "Aiber Update"})
    
@router.get("/activated", name="activation_page")
def activation_page(request: Request, db: Session = Depends(get_db)):
    """Serve the Admin page"""
    email = None
    try:
        token = request.query_params.get("token")
        payload = decode_access_token(token)
        email = payload.get("sub")
        if email is None:
            status = "Неверный Код активации"
    except Exception as e:
        status = "Неверный Код активации"
    
    if email:
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        if not user:
            status = "Аккаунт не найден."
        
        status = "Ваш аккаунт Активирован"
        if user.is_active:
            status = "Эл. почу уже была подтверждена, Вы Активированы"
        
        user.is_active = True
        db.commit()
    
    return templates.TemplateResponse("auth/activated.html", {"title": "Aiber Auth", "status": status})

@router.get("/contacts", name="contact_page")
def contact_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Login page"""
    return templates.TemplateResponse("auth/contact.html", {**context, "title": "Aiber Contacts"})

@router.get("/login", name="login_page")
def about_page(request: Request, context: dict = Depends(global_context)):
    """Serve the Login page"""
    return templates.TemplateResponse("auth/login.html", {**context, "title": "Aiber Login"})

@router.get("/about")
def contact_page(request: Request, context: dict = Depends(global_context)):
    """Serve the About page"""
    curr_user = context.get("current_user")
    if not curr_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("auth/about.html", {**context, "title": "Aiber Profile"})

@router.get("/register", name="register_page")
def register_page(request: Request, context: dict = Depends(global_context)):
    """Serves the registration page."""
    return templates.TemplateResponse("auth/register.html", {**context, "title": "Aiber Auth"})