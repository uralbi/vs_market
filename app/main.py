from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from app.core.config import settings
from app.api.routes import users, entiities
from app.web.routes import web_routes
import logging
import logging.config

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(web_routes.router)
app.include_router(entiities.router)
app.include_router(users.router)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

@app.get("/")
def read_root():
    return {"App": "Authentication"}
