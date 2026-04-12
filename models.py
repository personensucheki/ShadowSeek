
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class PublicProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, index=True)
    platform = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(32), nullable=False)  # z. B. "social", "dating", "adult", "porn"
    profile_url = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(255), nullable=True)
    last_found = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<PublicProfile {self.username} on {self.platform} ({self.category})>'


# User model
class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Erweiterte Profilfelder
    title = db.Column(db.String(120), default="SuperAdmin | Eigentümer | Support")
    bio = db.Column(db.Text, default="Ich bin der Eigentümer von ShadowSeek, SuperAdmin und für Support zuständig. Bei Anliegen oder Spenden bitte direkt kontaktieren.")
    avatar_url = db.Column(db.String(255), default="/static/avatar_admin.png")
    banner_url = db.Column(db.String(255), default="/static/banner_admin.png")
    support_contact = db.Column(db.String(120), default="personensucheki@gmail.com")
    spenden_link = db.Column(db.String(255), default="https://paypal.me/personensucheki")
    birthdate = db.Column(db.String(32), default="12.04.2026")
    height_cm = db.Column(db.Integer, default=187)

    def __repr__(self):
        return f'<User {self.username}>'
