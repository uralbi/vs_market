from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
import os

router = APIRouter(    
    prefix='',
    tags=['Websites'])


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "../templates"))


@router.get("/login", name="login_page")
def about_page(request: Request):
    """Serve the Login page"""
    return templates.TemplateResponse("login.html", {"request": request, "title": "Login"})

@router.get("/about")
def contact_page(request: Request):
    """Serve the About page"""
    return templates.TemplateResponse("about.html", {"request": request, "title": "About"})

@router.get("/register", name="register_page")
def register_page(request: Request):
    """Serves the registration page."""
    return templates.TemplateResponse("register.html", {"request": request})