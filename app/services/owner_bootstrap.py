from __future__ import annotations

from sqlalchemy.exc import OperationalError

from app.extensions import db
from app.models.user import User


def _is_enabled(raw_value) -> bool:
    return str(raw_value).strip().lower() in {"1", "true", "yes", "on"}


def _ensure_tables_exist() -> None:
    """Best-effort table bootstrap for first runs.

    Render/Prod Deployments können starten, bevor Migrationen ausgeführt wurden.
    In diesem Fall würde der Owner-Account nicht angelegt werden und der Login
    schlägt dauerhaft fehl. Wir versuchen daher einmalig, die Tabellen zu
    erstellen (nur falls sie fehlen) und legen dann den Owner an.
    """

    try:
        db.create_all()
    except Exception:  # pragma: no cover
        # create_all kann fehlschlagen (z.B. fehlende Rechte in Postgres).
        # Das darf den App-Start nicht blockieren; Logging passiert im Caller.
        return


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
    except OperationalError as exc:  # pragma: no cover
        db.session.rollback()
        # Typischer Erststart-Fehler: Tabelle existiert noch nicht.
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
