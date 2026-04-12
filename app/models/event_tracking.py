"""
Event-Tracking-Modelle für Feed- und Live-Events
"""
from app.extensions.main import db
from datetime import datetime

class FeedImpression(db.Model):
    __tablename__ = "feed_impressions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("media_posts.id"), nullable=False, index=True)
    event_type = db.Column(db.String(32), nullable=False)  # impression, video_start, 25_percent, ...
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    meta = db.Column(db.JSON, nullable=True)

class UserInteraction(db.Model):
    __tablename__ = "user_interactions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey("media_posts.id"), nullable=True, index=True)
    live_session_id = db.Column(db.Integer, db.ForeignKey("live_sessions.id"), nullable=True, index=True)
    event_type = db.Column(db.String(32), nullable=False)  # like, comment, share, ...
    value = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    meta = db.Column(db.JSON, nullable=True)

class LiveSession(db.Model):
    __tablename__ = "live_sessions"
    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(255), nullable=True)
    platform = db.Column(db.String(32), nullable=True)
    meta = db.Column(db.JSON, nullable=True)

class LiveMetric(db.Model):
    __tablename__ = "live_metrics"
    id = db.Column(db.Integer, primary_key=True)
    live_session_id = db.Column(db.Integer, db.ForeignKey("live_sessions.id"), nullable=False, index=True)
    event_type = db.Column(db.String(32), nullable=False)  # live_impression, join_live, ...
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
    value = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    meta = db.Column(db.JSON, nullable=True)
