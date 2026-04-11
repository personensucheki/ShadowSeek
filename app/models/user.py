from datetime import datetime
from ..extensions import db

from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(32), nullable=False, default='user', index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    display_name = db.Column(db.String(80), unique=False, nullable=True)
    bio = db.Column(db.String(500), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Billing/Subscription
    stripe_customer_id = db.Column(db.String(64), nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(64), nullable=True, index=True)
    plan_code = db.Column(db.String(32), nullable=True, index=True)
    subscription_status = db.Column(db.String(32), nullable=True)
    subscription_period_end = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role):
        return self.role == role

    def has_permission(self, permission):
        from app.rbac import role_has_permission
        return role_has_permission(self.role, permission)

    def is_super_admin(self):
        return self.role == 'super_admin'

    def is_admin(self):
        return self.role in ('admin', 'super_admin')

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar": self.avatar,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }
