
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

celery:
	celery -A app.infra.celery_fld.celery_app worker --loglevel=info

