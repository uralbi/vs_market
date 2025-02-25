
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

celery:
	celery -A app.infra.celery_fld.celery_config.celery_app worker --loglevel=info

kafka_topics:
	/opt/homebrew/opt/kafka/bin/kafka-topics --bootstrap-server 127.0.0.1:9092 --list

