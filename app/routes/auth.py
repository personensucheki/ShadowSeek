from flask import Blueprint, flash, redirect, request, session, url_for, jsonify
from flask import current_app

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

    # SuperAdmin darf nicht registriert werden
    if email.lower() == "personensucheki@gmail.com" or username.upper() == "ADMIN":
        flash("Registrierung dieses Benutzers ist nicht erlaubt.", "danger")
        return redirect(url_for("search.home"))

    if not username or not email or not password:
        flash("Alle Felder sind erforderlich.", "danger")
        return redirect(url_for("search.home"))

    if User.query.filter_by(username=username).first():
        flash("Username existiert bereits.", "danger")
        return redirect(url_for("search.home"))

    if User.query.filter_by(email=email).first():
        flash("E-Mail existiert bereits.", "danger")
        return redirect(url_for("search.home"))

    user = User(username=username, email=email, is_verified=False, is_active=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    # Verifizierungs-Token generieren
    from itsdangerous import URLSafeTimedSerializer
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    token = s.dumps({"user_id": user.id}, salt="email-verify")

    # E-Mail-Versand (Dummy SMTP)
    from smtplib import SMTP
    from email.mime.text import MIMEText
    verify_url = url_for("auth.verify_email", token=token, _external=True)
    msg = MIMEText(f"Hallo {username},\n\nBitte bestätige deine Registrierung bei ShadowSeek, indem du auf folgenden Link klickst:\n{verify_url}\n\nDein ShadowSeek Team")
    msg["Subject"] = "ShadowSeek Registrierung bestätigen"
    msg["From"] = "noreply@shadowseek.de"
    msg["To"] = email
    try:
        with SMTP("localhost") as smtp:
            smtp.sendmail(msg["From"], [msg["To"]], msg.as_string())
    except Exception as e:
        flash(f"Fehler beim Senden der Bestätigungs-Mail: {e}", "danger")
        return redirect(url_for("search.home"))

    flash("Bitte bestätige deine E-Mail-Adresse. Prüfe dein Postfach!", "info")
    return redirect(url_for("search.home"))

@auth_bp.route("/verify/<token>")
def verify_email(token):
    from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        data = s.loads(token, salt="email-verify", max_age=86400)
        user_id = data["user_id"]
    except (BadSignature, SignatureExpired):
        flash("Der Bestätigungslink ist ungültig oder abgelaufen.", "danger")
        return redirect(url_for("search.home"))
    user = User.query.get(user_id)
    if not user:
        flash("Benutzer nicht gefunden.", "danger")
        return redirect(url_for("search.home"))
    if user.is_verified:
        flash("Dein Konto ist bereits bestätigt.", "info")
        return redirect(url_for("search.home"))
    user.is_verified = True
    user.is_active = True
    db.session.commit()
    session["user_id"] = user.id
    session["role"] = user.role
    session["is_admin"] = user.is_admin()
    flash("E-Mail bestätigt! Willkommen, du bist jetzt eingeloggt.", "success")
    return redirect(url_for("dashboard.dashboard"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return redirect(url_for("search.home"))

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    # SuperAdmin kann sich nur mit ADMIN anmelden
    user = User.query.filter((User.username == username) | (User.email == username)).first()

    if not user or not user.check_password(password):
        flash("Ungueltige Zugangsdaten.", "danger")
        return redirect(url_for("search.home"))

    session["user_id"] = user.id
    session["role"] = user.role
    if user.is_super_admin():
        session["is_admin"] = True
    elif user.is_admin():
        session["is_admin"] = True
    else:
        session["is_admin"] = False

    flash("Login erfolgreich.", "success")
    return redirect(url_for("search.search"))


@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("role", None)
    session.pop("is_admin", None)
    flash("Abgemeldet.", "info")
    return redirect(url_for("search.home"))


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    flash("Passwort-Reset ist noch nicht aktiviert.", "info")
    return redirect(url_for("search.home"))


@auth_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    password = data.get('password', '')
    user = User.query.filter((User.username==username)|(User.email==username)).first()
    if not user or not user.check_password(password):
        return jsonify(success=False, message='Login fehlgeschlagen. Prüfe Benutzerdaten.')
    session['user_id'] = user.id
    session['username'] = user.username
    return jsonify(success=True, message='Login erfolgreich! Weiterleitung ...')

@auth_bp.route('/register', methods=['POST'])
def api_register():
    data = request.get_json() or request.form
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    if len(username) < 3:
        return jsonify(success=False, message='Benutzername zu kurz (min. 3 Zeichen).')
    if len(password) < 6:
        return jsonify(success=False, message='Passwort zu kurz (min. 6 Zeichen).')
    if User.query.filter_by(username=username).first():
        return jsonify(success=False, message='Benutzername existiert bereits.')
    if User.query.filter_by(email=email).first():
        return jsonify(success=False, message='E-Mail existiert bereits.')
    user = User(username=username, email=email, is_verified=False, is_active=False)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify(success=True, message='Registrierung erfolgreich! Bitte logge dich ein.')
