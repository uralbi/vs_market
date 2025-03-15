from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import users, entiities, products, favorites, chat, video
from app.api.websockets import chat_ws2
from app.web.routes import web_routes, web_product_routes, web_v_routes
from fastapi.middleware.cors import CORSMiddleware
from app.domain.security.signed_url import create_encryption_keyinfo
from contextlib import asynccontextmanager
from app.infra.redis_fld.redis_config import set_eviction_policy
from dotenv import load_dotenv
from app.core.config import settings
import logging, os
import logging.config

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)
load_dotenv()

DOMAIN = os.getenv("DOMAIN")
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources (like Redis) on startup and clean up on shutdown."""
    await set_eviction_policy("volatile-lru")
    yield                                       

app = FastAPI(lifespan=lifespan)

create_encryption_keyinfo()

BLOCKED_IPS = {"192.168.1.100", "203.0.113.42"} 

# Middleware to block restricted IPs
# @app.middleware("http")
# async def block_ip_middleware(request: Request, call_next):
#     client_ip = request.client.host  # Get client IP
#     if client_ip in BLOCKED_IPS:
#         raise HTTPException(status_code=403, detail="Access denied from this IP")
#     return await call_next(request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # Only allow your domain
    allow_credentials=True,
    allow_methods=["GET"],  # Restrict allowed methods
    allow_headers=["*"],    # Allow all headers
)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.mount("/media", StaticFiles(directory="media/movies/thumbs"), name="media")

@app.get("/play-audio/{filename}")
async def serve_audio(filename: str, request: Request):
    """
    Serve audio files for playback but block direct downloads.
    """
    file_path = f"app/web/static/mp3/{filename}"
    referer = request.headers.get("referer")
    if not referer:  
        raise HTTPException(status_code=403, detail="Access denied")

    return FileResponse(file_path, media_type="audio/mpeg", filename=filename, headers={
        "Content-Disposition": "inline",  # Prevents forcing download
        "Cache-Control": "no-store"
    })
    
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
