from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, send_from_directory, session, url_for
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models.user import User
from app.services.search_service import list_platform_cards
from app.services.media import resolve_user_avatar_url, resolve_user_banner_url


profile_bp = Blueprint("profile", __name__)

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _json_error(message: str, status_code: int = 400):
    return jsonify(success=False, message=message), status_code


def _normalize_text(value: str, max_len: int | None = None):
    text = (value or "").strip()
    if max_len is not None:
        return text[:max_len]
    return text


def _ensure_upload_dir(folder_name: str) -> Path:
    base_path = Path(current_app.config["UPLOAD_DIRECTORY"])
    target = base_path / folder_name
    target.mkdir(parents=True, exist_ok=True)
    return target


def _save_image(file_obj, user_id: int, kind: str):
    if not file_obj or not file_obj.filename:
        return None

    filename = secure_filename(file_obj.filename)
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Nur PNG, JPG, JPEG, WEBP oder GIF sind erlaubt.")

    folder = _ensure_upload_dir("avatars" if kind == "avatar" else "banners")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    stored_name = f"user_{user_id}_{kind}_{timestamp}{extension}"
    target = folder / stored_name
    file_obj.save(target)

    relative = "avatars" if kind == "avatar" else "banners"
    return f"{relative}/{stored_name}"


@profile_bp.route("/uploads/<path:filename>", methods=["GET"])
def uploaded_file(filename: str):
    """Serve uploaded media files.

    On Render this MUST be backed by a persistent disk via UPLOAD_DIRECTORY,
    otherwise images will disappear after restart.
    """
    upload_root = Path(current_app.config["UPLOAD_DIRECTORY"])
    return send_from_directory(upload_root, filename, conditional=True)


def _read_social_accounts(form_data):
    accounts = {}
    for platform in list_platform_cards():
        key = f"social_{platform['slug']}"
        raw = _normalize_text(form_data.get(key, ""), 160)
        if raw:
            accounts[platform["slug"]] = raw
    return accounts


@profile_bp.route("/profile", methods=["GET"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("search.home"))

    user = User.query.get(session["user_id"])
    if not user:
        return redirect(url_for("search.home"))

    social_accounts = {}
    if user.social_accounts:
        try:
            social_accounts = json.loads(user.social_accounts)
        except (ValueError, TypeError):
            social_accounts = {}

    profile_avatar_url = resolve_user_avatar_url(user)
    profile_banner_url = resolve_user_banner_url(user)
    current_app.logger.debug(
        "profile_media user_id=%s avatar=%r banner=%r resolved_avatar=%s resolved_banner=%s",
        user.id,
        user.avatar,
        user.banner,
        profile_avatar_url,
        profile_banner_url,
    )

    return render_template(
        "profile.html",
        current_user=user,
        profile_platforms=list_platform_cards(),
        social_accounts=social_accounts,
        profile_avatar_url=profile_avatar_url,
        profile_banner_url=profile_banner_url,
    )


@profile_bp.route("/profile/update", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return _json_error("Nicht eingeloggt.", 401)

    user = User.query.get(session["user_id"])
    if not user:
        return _json_error("Benutzer nicht gefunden.", 404)

    data = request.form if request.form else (request.get_json(silent=True) or {})
    display_name = _normalize_text(data.get("display_name", ""), 80)
    email = _normalize_text(data.get("email", ""), 120).lower()
    bio = _normalize_text(data.get("bio", ""), 500)
    profile_title = _normalize_text(data.get("profile_title", ""), 120)
    gender = _normalize_text(data.get("gender", ""), 32)
    country = _normalize_text(data.get("country", ""), 80)
    city = _normalize_text(data.get("city", ""), 120)
    hobbies = _normalize_text(data.get("hobbies", ""), 1000)
    interests = _normalize_text(data.get("interests", ""), 1000)
    preferences = _normalize_text(data.get("preferences", ""), 1000)
    support_contact = _normalize_text(data.get("support_contact", ""), 255)
    donation_link = _normalize_text(data.get("donation_link", ""), 255)
    password = _normalize_text(data.get("password", ""))
    birthdate_raw = _normalize_text(data.get("birthdate", ""))
    height_raw = _normalize_text(data.get("height_cm", ""))

    if display_name and len(display_name) < 3:
        return _json_error("Display Name zu kurz (min. 3 Zeichen).")
    if email and not EMAIL_PATTERN.match(email):
        return _json_error("Ungueltige E-Mail.")
    if display_name and User.query.filter(User.display_name == display_name, User.id != user.id).first():
        return _json_error("Display Name existiert bereits.")
    if email and User.query.filter(User.email == email, User.id != user.id).first():
        return _json_error("E-Mail existiert bereits.")
    if password:
        if len(password) < 8:
            return _json_error("Passwort zu kurz (min. 8 Zeichen).")
        if (
            not re.search(r"[A-Z]", password)
            or not re.search(r"[a-z]", password)
            or not re.search(r"\d", password)
        ):
            return _json_error("Passwort braucht Gross-/Kleinbuchstaben und eine Zahl.")
    if donation_link and not URL_PATTERN.match(donation_link):
        return _json_error("Spenden-Link muss mit http:// oder https:// beginnen.")
    if support_contact and len(support_contact) < 3:
        return _json_error("Support-Kontakt ist zu kurz.")

    birthdate = None
    if birthdate_raw:
        try:
            birthdate = datetime.strptime(birthdate_raw, "%Y-%m-%d").date()
        except ValueError:
            return _json_error("Geburtsdatum ist ungueltig.")

    height_cm = None
    if height_raw:
        try:
            height_cm = int(height_raw)
        except ValueError:
            return _json_error("Koerpergroesse muss eine Zahl sein.")
        if height_cm < 80 or height_cm > 260:
            return _json_error("Koerpergroesse muss zwischen 80 und 260 cm liegen.")

    try:
        avatar_path = _save_image(request.files.get("avatar_upload"), user.id, "avatar")
        banner_path = _save_image(request.files.get("banner_upload"), user.id, "banner")
    except ValueError as error:
        return _json_error(str(error))

    if password:
        user.set_password(password)
    user.display_name = display_name or user.display_name
    user.email = email or user.email
    user.bio = bio
    user.profile_title = profile_title
    user.birthdate = birthdate
    user.gender = gender
    user.country = country
    user.city = city
    user.height_cm = height_cm
    user.hobbies = hobbies
    user.interests = interests
    user.preferences = preferences
    user.support_contact = support_contact
    user.donation_link = donation_link
    user.social_accounts = json.dumps(_read_social_accounts(data), ensure_ascii=True)
    if avatar_path:
        user.avatar = avatar_path
    if banner_path:
        user.banner = banner_path

    db.session.commit()
    return jsonify(success=True, message="Profil erfolgreich aktualisiert.")
