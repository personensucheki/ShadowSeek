from datetime import datetime

from app.extensions.main import db


class ProcessedWebhookEvent(db.Model):
    __tablename__ = "processed_webhook_event"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(128), unique=True, nullable=False, index=True)
    event_type = db.Column(db.String(128), nullable=False)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<ProcessedWebhookEvent {self.event_type}:{self.event_id}>"
