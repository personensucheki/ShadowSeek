from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions import db

class LiveStream(db.Model):
    __tablename__ = 'live_stream'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(40), nullable=False)
    game = db.Column(db.String(80))
    tags = db.Column(JSONB)
    allow_gifts = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LiveLike(db.Model):
    __tablename__ = 'live_like'
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('live_stream.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class LiveChatMessage(db.Model):
    __tablename__ = 'live_chat_message'
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('live_stream.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class LiveGift(db.Model):
    __tablename__ = 'live_gift'
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('live_stream.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gift_type = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
