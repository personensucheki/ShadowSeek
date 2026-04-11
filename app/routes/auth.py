from flask import Blueprint, flash, redirect, request, session, url_for

from ..extensions import db
from ..models.user import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return redirect(url_for("search.home"))

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "").strip()

    if not username or not email or not password:
        flash("Alle Felder sind erforderlich.", "danger")
        return redirect(url_for("search.home"))

    if User.query.filter_by(username=username).first():
        flash("Username existiert bereits.", "danger")
        return redirect(url_for("search.home"))

    if User.query.filter_by(email=email).first():
        flash("E-Mail existiert bereits.", "danger")
        return redirect(url_for("search.home"))

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("Registrierung erfolgreich. Bitte anmelden.", "success")
    return redirect(url_for("search.home"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return redirect(url_for("search.home"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        flash("Ungueltige Zugangsdaten.", "danger")
        return redirect(url_for("search.home"))

    session["user_id"] = user.id
    flash("Login erfolgreich.", "success")
    return redirect(url_for("search.search"))


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Abgemeldet.", "info")
    return redirect(url_for("search.home"))


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    flash("Passwort-Reset ist noch nicht aktiviert.", "info")
    return redirect(url_for("search.home"))
