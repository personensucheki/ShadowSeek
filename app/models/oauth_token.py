from datetime import datetime

from app.extensions.main import db


class OAuthToken(db.Model):
    __tablename__ = "oauth_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    provider = db.Column(db.String(32), nullable=False, index=True)

    access_token_enc = db.Column(db.Text, nullable=False)
    refresh_token_enc = db.Column(db.Text, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    scope = db.Column(db.Text, nullable=True)
    token_type = db.Column(db.String(32), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "provider", name="uq_oauth_token_user_provider"),
    )

