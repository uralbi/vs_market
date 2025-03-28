
run:
	uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --log-level debug

celery:
	celery -A app.infra.celery_fld.celery_config.celery_app worker --loglevel=info

kafka_topics:
	/opt/homebrew/opt/kafka/bin/kafka-topics --bootstrap-server 127.0.0.1:9092 --list

web:
	CODE app/web