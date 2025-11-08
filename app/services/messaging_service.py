from app.infra.kafka_producer import send_event

class MessagingService:
    def send_new_message_notification(self, user_id: str, message: str):
        event = {"user_id": user_id, "message": message}
        send_event("notifications", event)

