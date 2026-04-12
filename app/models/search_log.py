from datetime import datetime
from app.extensions.main import db

class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    query = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(32), nullable=True)
    filters_json = db.Column(db.Text, nullable=True)
    result_count = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
