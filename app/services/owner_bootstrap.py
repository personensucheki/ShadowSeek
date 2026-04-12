from __future__ import annotations

from app.extensions import db
from app.models.user import User


def _is_enabled(raw_value) -> bool:
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def ensure_owner_account(app):
    enabled = _is_enabled(app.config.get("OWNER_BOOTSTRAP_ENABLED"))
    if not enabled:
        return

    username = (app.config.get("OWNER_BOOTSTRAP_USERNAME") or "").strip()
    email = (app.config.get("OWNER_BOOTSTRAP_EMAIL") or "").strip().lower()
    password = app.config.get("OWNER_BOOTSTRAP_PASSWORD") or ""

    if not username or not email or not password:
        app.logger.warning("Owner bootstrap enabled but username/email/password not fully configured.")
        return

    try:
        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user is None:
            user = User(username=username, email=email)
            db.session.add(user)

        user.username = username
        user.email = email
        user.role = "super_admin"
        user.is_active = True
        user.is_verified = True
        user.set_password(password)
        db.session.commit()
    except Exception as exc:  # pragma: no cover
        db.session.rollback()
        app.logger.warning("Owner bootstrap skipped: %s", exc)
