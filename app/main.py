from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import users, entiities, products, favorites, chat, video
from app.api.websockets import chat_ws2
from app.web.routes import web_routes, web_product_routes, web_v_routes
from fastapi.middleware.cors import CORSMiddleware
import logging
import logging.config

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)

app = FastAPI()


BLOCKED_IPS = {"192.168.1.100", "203.0.113.42"} 

# Middleware to block restricted IPs
# @app.middleware("http")
# async def block_ip_middleware(request: Request, call_next):
#     client_ip = request.client.host  # Get client IP
#     if client_ip in BLOCKED_IPS:
#         raise HTTPException(status_code=403, detail="Access denied from this IP")
#     return await call_next(request)


# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_ORIGINS,  # Only allow your domain
#     allow_credentials=True,
#     allow_methods=["GET"],  # Restrict allowed methods
#     allow_headers=["*"],    # Allow all headers
# )

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.mount("/media", StaticFiles(directory="media/movies/thumbs"), name="media")

app.include_router(video.router)
app.include_router(web_v_routes.router)
app.include_router(chat.router)
app.include_router(chat_ws2.router)
app.include_router(favorites.router)
app.include_router(web_product_routes.router)
app.include_router(web_routes.router)
app.include_router(products.router)
app.include_router(entiities.router)
app.include_router(users.router)

# @app.get("/app")
# def read_root():
#     return {"App": "Authentication"}
