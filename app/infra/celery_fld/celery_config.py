from celery import Celery

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0", 
    backend="redis://localhost:6379/0",
    include=["app.infra.tasks.email_tasks"]
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
