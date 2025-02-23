import os
from dotenv import load_dotenv
from celery.schedules import crontab
load_dotenv()


class Config:
    
    ALLOWED_ORIGINS = ["*"]
    
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND")
    CELERY_TASK_ROUTES: dict= {
        'tasks.*': {
            'queue': 'high_priority',
        },
        'low_priority_tasks.*': {
            'queue': 'low_priority',
        },
    }

    CELERY_BEAT_SCHEDULE: dict = {
        # "get_akinews": {
        #     "task": "Akinews",
        #     "schedule": crontab(hour=6, minute=45),  # Daily at 6 AM
        #     # "schedule": crontab(minute="*/1"),  # Run every 4 minutes
        #     'options': {'queue' : 'periodic'},
        # },
        # "get_24news": {
        #     "task": "24news",
        #     "schedule": crontab(hour=6, minute=52),  # Daily at 6 AM
        #     # "schedule": crontab(minute="*/2"),  # Run every 4 minutes
        #     'options': {'queue' : 'periodic'},
        # },
        # "get_econs": {
        #     "task": "econ_news",
        #     "schedule": crontab(hour=11, minute=53),  # Daily at 6 AM
        #     # "schedule": crontab(minute="*/2"),  # Run every 4 minutes
        #     'options': {'queue' : 'periodic'},
        # },
    }
    CELERY_TIMEZONE:str = "Asia/Bishkek"

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'timed_file': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'formatter': 'standard',
                'filename': os.environ.get("LOG_FILE"),
                'when': 'D',
                'interval': 1,
                'backupCount': 7,
            },
        },
        'formatters': {
            'standard': {
                'format': os.environ.get("LOG_FORMAT", "%(name)s - %(levelname)s - %(message)s"),
            },
        },
        'root': {
            'handlers': ['timed_file'],
            'level': os.environ.get("LOG_LEVEL", "WARNING"),
        },
    }

settings = Config()
