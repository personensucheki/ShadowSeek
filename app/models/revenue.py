from app.extensions import db
from datetime import datetime

from sqlalchemy.schema import UniqueConstraint

class RevenueEvent(db.Model):
    __tablename__ = "revenue_events"
    __table_args__ = (
        UniqueConstraint("platform", "username", "captured_at", "source", name="uq_revenue_event"),
    )
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), nullable=False)
    username = db.Column(db.String(64), nullable=False)
    display_name = db.Column(db.String(128))
    estimated_revenue = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(8), nullable=False)
    diamonds = db.Column(db.Integer)
    followers = db.Column(db.Integer)
    source = db.Column(db.String(64))
    confidence = db.Column(db.String(16))
    captured_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RevenueEvent {self.platform}:{self.username} {self.estimated_revenue} {self.currency}>"
