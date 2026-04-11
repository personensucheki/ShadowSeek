from app.extensions import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class EinnahmeInfo(db.Model):
    __tablename__ = "einnahme_info"
    __table_args__ = (
        UniqueConstraint("platform", "username", "captured_at", "source", name="uq_revenue_event"),
    )
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(32), default="unknown", nullable=False)
    username = db.Column(db.String(128), nullable=False)
    display_name = db.Column(db.String(128), nullable=True)
    estimated_revenue = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(16), default="EUR", nullable=False)
    captured_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    source = db.Column(db.String(128), nullable=False, default="scraper")
    confidence = db.Column(db.Float, nullable=False, default=0.5)
    betrag = db.Column(db.Float, nullable=False)
    waehrung = db.Column(db.String(16), default="EUR", nullable=False)
    typ = db.Column(db.String(32), default="tiktok_live", nullable=False)  # z.B. tiktok_live, diamonds, gifts
    quelle = db.Column(db.String(128), nullable=True)  # z.B. TikTok-Username
    details = db.Column(db.String(256), nullable=True) # z.B. Gift-Typ, Event
    zeitpunkt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EinnahmeInfo {self.betrag} {self.waehrung} {self.typ} @ {self.zeitpunkt}>"
