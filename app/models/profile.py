from datetime import datetime
from ..extensions import db

class PublicProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    platform = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    profile_url = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(255), nullable=True)
    last_found = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<PublicProfile {self.username} on {self.platform} ({self.category})>'
