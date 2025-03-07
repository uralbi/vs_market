from confluent_kafka import Producer
import json, os

KAFKA_CONFIG = {
    "bootstrap.servers": "127.0.0.1:9092",
    "acks": "all"  # Ensures messages are properly written before acknowledging
}

producer = Producer(KAFKA_CONFIG)

def delivery_report(err, msg):
    """ Callback for message delivery report """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

def send_kafka_message(topic: str, key: str, message: dict):
    """ Sends a message to Kafka with error handling """
    try:
        producer.produce(
            topic,
            key=key,
            value=json.dumps(message),
            callback=delivery_report
        )
        producer.flush()
    except Exception as e:
        print(f"❌ Kafka Error: {str(e)}")
