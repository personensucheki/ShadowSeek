from __future__ import annotations

from datetime import datetime

from app.extensions.main import db


class MediaPost(db.Model):
    __tablename__ = "media_posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    media_type = db.Column(db.String(16), nullable=False, index=True)  # "video" | "photo"
    file_path = db.Column(db.String(255), nullable=False)  # relative to UPLOAD_DIRECTORY
    caption = db.Column(db.String(500), nullable=True)

    hashtags = db.Column(db.String(400), nullable=True)  # Space-separierte Hashtags
    location = db.Column(db.String(120), nullable=True)
    trim_start = db.Column(db.Integer, nullable=True)
    trim_end = db.Column(db.Integer, nullable=True)

    is_public = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    like_count = db.Column(db.Integer, default=0, nullable=False)
    view_count = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", backref=db.backref("media_posts", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "media_type": self.media_type,
            "file_path": self.file_path,
            "caption": self.caption or "",
            "hashtags": self.hashtags or "",
            "location": self.location or "",
            "trim_start": self.trim_start,
            "trim_end": self.trim_end,
            "is_public": bool(self.is_public),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "like_count": int(self.like_count or 0),
            "view_count": int(self.view_count or 0),
        }

