from app.extensions.main import db
from datetime import datetime

class Match(db.Model):
    __tablename__ = 'match'
    id = db.Column(db.Integer, primary_key=True)
    user_a_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_b_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    matched_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')  # active, hidden, unmatched
    __table_args__ = (
        db.UniqueConstraint('user_a_id', 'user_b_id', name='uq_match_once'),
    )
