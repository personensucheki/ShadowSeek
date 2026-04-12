from __future__ import annotations

from functools import wraps

from flask import abort, g, jsonify, redirect, request, session, url_for

from app.models.user import User
from app.services.billing import billing_enabled
from app.services.permissions import has_any_permission, has_permission


def _current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    from app.extensions.main import db

    user = db.session.get(User, user_id)
    return user


def _wants_json():
    return request.path.startswith("/api/") or request.is_json


def feature_required(feature: str, *, redirect_to_billing: bool = True):
    """
    Serverseitiger Guard für Premium-Features.
    - Für API: 401/403 JSON
    - Für Pages: redirect auf Billing-Seite (oder 403, wenn redirect_to_billing=False)
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = getattr(g, "current_user", None) or _current_user()
            g.current_user = user

            if not billing_enabled():
                return f(*args, **kwargs)

            if not user:
                if _wants_json():
                    return jsonify({"success": False, "error": "Bitte zuerst anmelden."}), 401
                return redirect(url_for("billing.billing_page"))

            if not has_permission(user, feature):
                if _wants_json():
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "Dein aktuelles Abo erlaubt dieses Feature nicht.",
                                "missing_feature": feature,
                                "feature_gating": True,
                            }
                        ),
                        403,
                    )
                if redirect_to_billing:
                    return redirect(url_for("billing.billing_page"))
                abort(403)

            return f(*args, **kwargs)

        return wrapped

    return decorator


def any_feature_required(*features: str, redirect_to_billing: bool = True):
    """
    Wie feature_required, aber akzeptiert eine Liste: mindestens eins muss erlaubt sein.
    """

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            user = getattr(g, "current_user", None) or _current_user()
            g.current_user = user

            if not billing_enabled():
                return f(*args, **kwargs)

            if not user:
                if _wants_json():
                    return jsonify({"success": False, "error": "Bitte zuerst anmelden."}), 401
                return redirect(url_for("billing.billing_page"))

            if not has_any_permission(user, *features):
                if _wants_json():
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": "Dein aktuelles Abo erlaubt dieses Feature nicht.",
                                "missing_any_of": list(features),
                                "feature_gating": True,
                            }
                        ),
                        403,
                    )
                if redirect_to_billing:
                    return redirect(url_for("billing.billing_page"))
                abort(403)

            return f(*args, **kwargs)

        return wrapped

    return decorator
