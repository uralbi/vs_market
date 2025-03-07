from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

celery_app = Celery(
    "tasks",
    # broker="redis://localhost:6377/0", 
    # backend="redis://localhost:6377/0",
    broker = os.getenv("CELERY_BROKER_URL"),
    backend = os.getenv("CELERY_RESULT_BACKEND"),
    include=["app.infra.tasks.email_tasks", "app.infra.tasks.vid_tasks"]
)

# celery_app.conf.task_routes = {
#     "send_verification_email": {"queue": "email_queue"},
#     "send_notification_email": {"queue": "email_queue"}
# }

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)
