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
    profile_title = db.Column(db.String(120), nullable=True)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(32), nullable=True)
    country = db.Column(db.String(80), nullable=True, index=True)
    city = db.Column(db.String(120), nullable=True)
    height_cm = db.Column(db.Integer, nullable=True)
    hobbies = db.Column(db.String(1000), nullable=True)
    interests = db.Column(db.String(1000), nullable=True)
    preferences = db.Column(db.String(1000), nullable=True)
    social_accounts = db.Column(db.Text, nullable=True)
    support_contact = db.Column(db.String(255), nullable=True)
    donation_link = db.Column(db.String(255), nullable=True)
    avatar = db.Column(db.String(255), nullable=True)
    banner = db.Column(db.String(255), nullable=True)
    last_seen_at = db.Column(db.DateTime, nullable=True, index=True)
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

    @property
    def age(self):
        if not self.birthdate:
            return None
        today = datetime.utcnow().date()
        return today.year - self.birthdate.year - (
            (today.month, today.day) < (self.birthdate.month, self.birthdate.day)
        )

    @property
    def is_online(self):
        if not self.last_seen_at:
            return False
        return (datetime.utcnow() - self.last_seen_at).total_seconds() <= 300

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "bio": self.bio,
            "profile_title": self.profile_title,
            "birthdate": self.birthdate.isoformat() if self.birthdate else None,
            "age": self.age,
            "gender": self.gender,
            "country": self.country,
            "city": self.city,
            "height_cm": self.height_cm,
            "hobbies": self.hobbies,
            "interests": self.interests,
            "preferences": self.preferences,
            "social_accounts": self.social_accounts,
            "support_contact": self.support_contact,
            "donation_link": self.donation_link,
            "avatar": self.avatar,
            "banner": self.banner,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "is_online": self.is_online,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_active": self.is_active,
        }
