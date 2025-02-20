from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.api.routes import users, entiities, products, favorites, chat
from app.api.websockets import chat_ws2
from app.web.routes import web_routes, web_product_routes, web_v_routes
import logging
import logging.config

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

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
