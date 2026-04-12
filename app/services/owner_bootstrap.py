from __future__ import annotations

from sqlalchemy.exc import OperationalError

from app.extensions.main import db
from app.models.user import User


def _is_enabled(raw_value) -> bool:
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def _ensure_tables_exist() -> None:
    """
    Fallback for first-boot scenarios where migrations haven't been applied yet.
    Only used when the owner bootstrap hits an OperationalError.
    """
    try:
        db.create_all()
    except Exception:
        db.session.rollback()


def ensure_owner_account(app):
    """
    Creates/updates a single "owner" account (super_admin) from environment config.

    Render/Prod setup (Environment Variables):
    - OWNER_BOOTSTRAP_ENABLED=1
    - OWNER_BOOTSTRAP_USERNAME=ADMIN
    - OWNER_BOOTSTRAP_EMAIL=admin@example.com
    - OWNER_BOOTSTRAP_PASSWORD=... (mind. 8 Zeichen)
    """

    enabled = _is_enabled(app.config.get("OWNER_BOOTSTRAP_ENABLED"))
    if not enabled:
        return

    username = (app.config.get("OWNER_BOOTSTRAP_USERNAME") or "").strip()
    email = (app.config.get("OWNER_BOOTSTRAP_EMAIL") or "").strip().lower()
    password = app.config.get("OWNER_BOOTSTRAP_PASSWORD") or ""

    if not username or not email or not password:
        app.logger.warning(
            "Owner bootstrap enabled but username/email/password not fully configured."
        )
        return

    if len(password) < 8:
        app.logger.warning("Owner bootstrap password too short; skipping.")
        return

    try:
        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user is None:
            user = User(username=username, email=email)
            db.session.add(user)

        # Standard-Profilwerte
        user.username = username
        user.email = email
        user.role = "super_admin"
        user.is_active = True
        user.is_verified = True
        user.set_password(password)
        user.display_name = "Admin"
        user.profile_title = "SuperAdmin | Eigentumer | Support"
        user.bio = "Ich bin der Eigentumer von ShadowSeek, SuperAdmin und fuer Support zustaendig. Bei Anliegen oder Spenden bitte direkt kontaktieren."
        user.birthdate = datetime(2026, 4, 12).date()
        user.gender = "Männlich"
        user.country = ""
        user.city = ""
        user.height_cm = 187
        user.hobbies = ""
        user.interests = ""
        user.preferences = ""
        user.support_contact = "personensucheki@gmail.com"
        user.donation_link = "https://paypal.me/personensucheki"
        user.social_accounts = "{}"
        # Avatar und Banner setzen
        user.avatar = "avatars/user_1_avatar_20260412000000.png"
        user.banner = "banners/user_1_banner_20260412000000.png"
        db.session.commit()
    except OperationalError as exc:  # pragma: no cover
        db.session.rollback()
        app.logger.warning("Owner bootstrap hit DB error, trying create_all(): %s", exc)
        _ensure_tables_exist()
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
        except Exception as second_exc:
            db.session.rollback()
            app.logger.warning("Owner bootstrap skipped after retry: %s", second_exc)
    except Exception as exc:  # pragma: no cover
        db.session.rollback()
        app.logger.warning("Owner bootstrap skipped: %s", exc)

