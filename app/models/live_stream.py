from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from app.extensions.main import db

from sqlalchemy import Enum as PgEnum

class LiveStreamStatus:
    DRAFT = "draft"
    PROVISIONING = "provisioning"
    READY = "ready"
    LIVE = "live"
    ENDED = "ended"
    ERROR = "error"

class LiveStream(db.Model):
    __tablename__ = 'live_stream'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(40), nullable=False)
    game = db.Column(db.String(80))
    tags = db.Column(db.JSON)
    allow_gifts = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Provider-Integration
    provider = db.Column(db.String(32), nullable=True, index=True)
    provider_input_id = db.Column(db.String(128), nullable=True, index=True)
    provider_channel_id = db.Column(db.String(128), nullable=True, index=True)
    ingest_url = db.Column(db.String(512), nullable=True)
    playback_url = db.Column(db.String(512), nullable=True)
    provider_status = db.Column(PgEnum(
        LiveStreamStatus.DRAFT,
        LiveStreamStatus.PROVISIONING,
        LiveStreamStatus.READY,
        LiveStreamStatus.LIVE,
        LiveStreamStatus.ENDED,
        LiveStreamStatus.ERROR,
        name="live_stream_status"
    ), default=LiveStreamStatus.DRAFT, nullable=False)
    provider_output_bucket = db.Column(db.String(128), nullable=True)
    location = db.Column(db.String(64), nullable=True)
    stream_key = db.Column(db.String(128), nullable=True)

class LiveLike(db.Model):
    __tablename__ = 'live_like'
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('live_stream.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class LiveChatMessage(db.Model):
    __tablename__ = 'live_chat_message'
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('live_stream.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class LiveGift(db.Model):
    __tablename__ = 'live_gift'
    id = db.Column(db.Integer, primary_key=True)
    stream_id = db.Column(db.Integer, db.ForeignKey('live_stream.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gift_type = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Integer, default=1)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
