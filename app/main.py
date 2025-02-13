from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from app.core.config import settings
from app.api.routes import users, entiities, products
from app.web.routes import web_routes, web_product_routes
import logging
import logging.config

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

app.include_router(web_product_routes.router)
app.include_router(web_routes.router)
app.include_router(products.router)
app.include_router(entiities.router)
app.include_router(users.router)

# @app.get("/app")
# def read_root():
#     return {"App": "Authentication"}
