from app.extensions.main import db
from datetime import datetime

class SwipeAction(db.Model):
    __tablename__ = 'swipe_action'
    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(10), nullable=False)  # left, right, super
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('actor_user_id', 'target_user_id', name='uq_swipe_once'),
    )
