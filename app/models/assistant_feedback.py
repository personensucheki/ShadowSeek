from datetime import datetime
from app.extensions import db

class AssistantFeedback(db.Model):
    __tablename__ = "assistant_feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    assistant_reply = db.Column(db.Text, nullable=False)
    search_context_json = db.Column(db.Text, nullable=True)
    feedback_score = db.Column(db.Integer, nullable=True)  # 1=hilfreich, 0=nicht hilfreich, -1=nochmal, -2=besser erklären
    intent_label = db.Column(db.String(64), nullable=True)
    resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AssistantFeedback {self.id} intent={self.intent_label} score={self.feedback_score}>"
