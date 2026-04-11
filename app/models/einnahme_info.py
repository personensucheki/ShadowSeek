from app.extensions import db
from datetime import datetime

class EinnahmeInfo(db.Model):
    __tablename__ = "einnahme_info"
    id = db.Column(db.Integer, primary_key=True)
    betrag = db.Column(db.Float, nullable=False)
    waehrung = db.Column(db.String(16), default="EUR", nullable=False)
    typ = db.Column(db.String(32), default="tiktok_live", nullable=False)  # z.B. tiktok_live, diamonds, gifts
    quelle = db.Column(db.String(128), nullable=True)  # z.B. TikTok-Username
    details = db.Column(db.String(256), nullable=True) # z.B. Gift-Typ, Event
    zeitpunkt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<EinnahmeInfo {self.betrag} {self.waehrung} {self.typ} @ {self.zeitpunkt}>"
