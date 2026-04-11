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

    @staticmethod
    def redact_sensitive(text):
        # Einfache Maskierung für offensichtliche sensible Daten (z.B. E-Mail, Telefonnummer)
        import re
        if not text:
            return text
        # E-Mail
        text = re.sub(r"[\w\.-]+@[\w\.-]+", "[email]", text)
        # Telefonnummern
        text = re.sub(r"\b\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b", "[phone]", text)
        return text

    @classmethod
    def create_safe(cls, **kwargs):
        # Maskiere sensible Daten
        kwargs["user_message"] = cls.redact_sensitive(kwargs.get("user_message"))
        kwargs["assistant_reply"] = cls.redact_sensitive(kwargs.get("assistant_reply"))
        return cls(**kwargs)

    @classmethod
    def delete_older_than(cls, db, days=90):
        from datetime import datetime, timedelta
        threshold = datetime.utcnow() - timedelta(days=days)
        db.session.query(cls).filter(cls.created_at < threshold).delete()
        db.session.commit()

    def __repr__(self):
        return f"<AssistantFeedback {self.id} intent={self.intent_label} score={self.feedback_score}>"
