from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class PublicProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    platform = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(32), nullable=False)  # z. B. "social", "dating", "adult", "porn"
    profile_url = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(255), nullable=True)
    last_found = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<PublicProfile {self.username} on {self.platform} ({self.category})>'
