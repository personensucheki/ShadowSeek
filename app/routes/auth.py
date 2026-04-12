from __future__ import annotations

import re

from flask import Blueprint, jsonify, redirect, request, session, url_for

from app.extensions.main import db
from ..extensions.main import csrf
from ..models.user import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _wants_json_response() -> bool:
    if request.is_json:
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in accept.lower()


def _payload_value(data: dict, key: str) -> str:
    value = data.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def _auth_response(success: bool, message: str, *, redirect_to: str, status_code: int = 200):
    if _wants_json_response():
        return (
            jsonify(
                success=success,
                message=message,
                redirect=redirect_to if success else None,
            ),
            status_code,
        )

    if success:
        return redirect(redirect_to)
    return redirect(url_for("search.home"))


def _set_auth_session(user: User) -> None:
    session["user_id"] = user.id
    session["username"] = user.username
    session["role"] = user.role
    session["is_admin"] = user.role in ("super_admin", "admin")


@auth_bp.route("/register", methods=["GET", "POST"])
@csrf.exempt
def register():
    if request.method == "GET":
        return redirect(url_for("search.home"))

    data = request.get_json(silent=True) if request.is_json else request.form

    username = _payload_value(data, "username")
    email = _payload_value(data, "email").lower()
    password = _payload_value(data, "password")
    password2 = _payload_value(data, "password2")

    if not username or not email or not password:
        return _auth_response(
            False,
            "Bitte Benutzername, E-Mail und Passwort ausfuellen.",
            redirect_to=url_for("search.home"),
            status_code=400,
        )
    if len(username) < 3:
        return _auth_response(
            False,
            "Benutzername zu kurz (mindestens 3 Zeichen).",
            redirect_to=url_for("search.home"),
            status_code=400,
        )
    if len(password) < 8:
        return _auth_response(
            False,
            "Passwort zu kurz (mindestens 8 Zeichen).",
            redirect_to=url_for("search.home"),
            status_code=400,
        )
    if password2 and password != password2:
        return _auth_response(
            False,
            "Passwoerter stimmen nicht ueberein.",
            redirect_to=url_for("search.home"),
            status_code=400,
        )
    if not EMAIL_PATTERN.match(email):
        return _auth_response(
            False,
            "Bitte eine gueltige E-Mail angeben.",
            redirect_to=url_for("search.home"),
            status_code=400,
        )

    if username.upper() == "ADMIN" or email == "personensucheki@gmail.com":
        return _auth_response(
            False,
            "Dieser Benutzername oder diese E-Mail ist reserviert. Bitte mit dem Eigentuemer-Account anmelden.",
            redirect_to=url_for("search.home"),
            status_code=403,
        )

    if User.query.filter_by(username=username).first():
        return _auth_response(
            False,
            "Benutzername existiert bereits.",
            redirect_to=url_for("search.home"),
            status_code=409,
        )
    if User.query.filter_by(email=email).first():
        return _auth_response(
            False,
            "E-Mail existiert bereits.",
            redirect_to=url_for("search.home"),
            status_code=409,
        )

    user = User(
        username=username,
        email=email,
        role="user",
        is_verified=True,
        is_active=True,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    _set_auth_session(user)
    return _auth_response(
        True,
        "Registrierung erfolgreich.",
        redirect_to=url_for("search.search"),
        status_code=201,
    )


@auth_bp.route("/login", methods=["GET", "POST"])
@csrf.exempt
def login():
    if request.method == "GET":
        return redirect(url_for("search.home"))

    data = request.get_json(silent=True) if request.is_json else request.form

    username = _payload_value(data, "username")
    password = _payload_value(data, "password")

    if not username or not password:
        return _auth_response(
            False,
            "Bitte Benutzername/E-Mail und Passwort angeben.",
            redirect_to=url_for("search.home"),
            status_code=400,
        )

    user = User.query.filter((User.username == username) | (User.email == username)).first()
    if not user or not user.check_password(password):
        return _auth_response(
            False,
            "Login fehlgeschlagen. Bitte Benutzerdaten pruefen.",
            redirect_to=url_for("search.home"),
            status_code=401,
        )

    if not user.is_active:
        return _auth_response(
            False,
            "Dein Konto ist deaktiviert.",
            redirect_to=url_for("search.home"),
            status_code=403,
        )

    _set_auth_session(user)
    return _auth_response(
        True,
        "Login erfolgreich.",
        redirect_to=url_for("search.search"),
    )


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("user_id", None)
    session.pop("username", None)
    session.pop("role", None)
    session.pop("is_admin", None)

    if _wants_json_response():
        return jsonify(success=True, message="Abgemeldet.", redirect=url_for("search.home"))
    return redirect(url_for("search.home"))


@auth_bp.route("/forgot-password", methods=["POST"])
@csrf.exempt
def forgot_password():
    return _auth_response(
        False,
        "Passwort-Reset ist aktuell noch nicht aktiviert.",
        redirect_to=url_for("search.home"),
        status_code=501,
    )
