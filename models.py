from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=True)
    lastname = db.Column(db.String(80), nullable=True)
    city = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    platform = db.Column(db.String(80), nullable=True)
    profile_pic = db.Column(db.String(255), nullable=True)
    info = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Profile {self.username}>'
