from fastapi.templating import Jinja2Templates
import os
from app.utils.temp_filters import time_ago, get_ids, tojson
from pathlib import Path

# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "../templates"))
# templates.env.filters["time_ago"] = time_ago

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "web" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["time_ago"] = time_ago
templates.env.filters["get_ids"] = get_ids
templates.env.filters["tojson"] = tojson