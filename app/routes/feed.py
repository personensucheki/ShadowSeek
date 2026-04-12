from __future__ import annotations

from datetime import datetime
from pathlib import Path

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from app.extensions.main import db
from app.models import MediaPost, User
from app.rbac_helpers import login_required
from app.services.media import resolve_user_avatar_url


feed_bp = Blueprint("feed", __name__)

ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
ALLOWED_PHOTO_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


def _uploads_root() -> Path:
    return Path(current_app.config["UPLOAD_DIRECTORY"]).resolve()


def _ensure_upload_dir(name: str) -> Path:
    target = _uploads_root() / name
    target.mkdir(parents=True, exist_ok=True)
    return target


def _save_media(file_obj, *, user_id: int, media_type: str) -> str:
    if not file_obj or not file_obj.filename:
        raise ValueError("Keine Datei erhalten.")

    # Videos dürfen größer sein als Avatar/Banner Uploads.
    max_size = int(current_app.config.get("MAX_VIDEO_UPLOAD_BYTES") or (60 * 1024 * 1024))
    file_obj.stream.seek(0, 2)
    size = file_obj.stream.tell()
    file_obj.stream.seek(0)
    if size > max_size:
        raise ValueError(f"Datei zu gross (max. {max_size // (1024 * 1024)} MB).")

    filename = secure_filename(file_obj.filename)
    ext = Path(filename).suffix.lower()
    if media_type == "video":
        allowed = ALLOWED_VIDEO_EXTENSIONS
        folder = "posts/videos"
    else:
        allowed = ALLOWED_PHOTO_EXTENSIONS
        folder = "posts/photos"
    if ext not in allowed:
        raise ValueError("Dateityp nicht erlaubt.")

    out_dir = _ensure_upload_dir(folder)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    stored_name = f"user_{user_id}_{media_type}_{ts}{ext}"
    target = out_dir / stored_name
    file_obj.save(target)
    return f"{folder}/{stored_name}"


@feed_bp.route("/feed", methods=["GET"])
def feed_page():
    return render_template("feed.html")


@feed_bp.route("/upload", methods=["GET"])
@login_required
def upload_page():
    return render_template("upload.html")


@feed_bp.route("/api/feed", methods=["GET"])
def api_feed():
    limit = min(max(int(request.args.get("limit", 12)), 1), 40)
    cursor = request.args.get("cursor")

    query = MediaPost.query.filter(MediaPost.is_public.is_(True)).order_by(MediaPost.created_at.desc())
    if cursor:
        try:
            cursor_id = int(cursor)
            query = query.filter(MediaPost.id < cursor_id)
        except ValueError:
            pass

    posts = query.limit(limit).all()
    user_ids = {post.user_id for post in posts}
    users = {user.id: user for user in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    items = []
    for post in posts:
        user = users.get(post.user_id)
        items.append(
            {
                **post.to_dict(),
                "username": user.username if user else "user",
                "display_name": (user.display_name or user.username) if user else "User",
                "avatar_url": resolve_user_avatar_url(user) if user else url_for("static", filename="images/default-avatar.png"),
                "media_url": url_for("profile.uploaded_file", filename=post.file_path),
                "profile_url": url_for("feed.public_profile", username=user.username) if user else None,
            }
        )

    next_cursor = str(posts[-1].id) if posts else None
    return jsonify({"success": True, "items": items, "next_cursor": next_cursor})


@feed_bp.route("/api/upload", methods=["POST"])
@login_required
def api_upload():
    user_id = session.get("user_id")
    user = db.session.get(User, user_id) if user_id else None
    if not user:
        return jsonify({"success": False, "error": "Nicht eingeloggt."}), 401

    media_type = (request.form.get("media_type") or "").strip().lower()
    if media_type not in {"video", "photo"}:
        return jsonify({"success": False, "error": "media_type muss 'video' oder 'photo' sein."}), 400

    caption = (request.form.get("caption") or "").strip()[:500]
    is_public = str(request.form.get("is_public") or "true").strip().lower() in {"1", "true", "yes", "on"}

    file_obj = request.files.get("file")
    try:
        stored_path = _save_media(file_obj, user_id=user.id, media_type=media_type)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    post = MediaPost(
        user_id=user.id,
        media_type=media_type,
        file_path=stored_path,
        caption=caption or None,
        is_public=is_public,
    )
    db.session.add(post)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "post": {
                **post.to_dict(),
                "media_url": url_for("profile.uploaded_file", filename=post.file_path),
            },
        }
    )


@feed_bp.route("/u/<string:username>", methods=["GET"])
def public_profile(username: str):
    user = User.query.filter(User.username == username, User.is_active.is_(True)).first_or_404()
    avatar_url = resolve_user_avatar_url(user)
    return render_template("profile_public.html", profile_user=user, avatar_url=avatar_url)


@feed_bp.route("/api/u/<string:username>/posts", methods=["GET"])
def api_user_posts(username: str):
    user = User.query.filter(User.username == username, User.is_active.is_(True)).first()
    if not user:
        return jsonify({"success": False, "error": "User nicht gefunden."}), 404

    limit = min(max(int(request.args.get("limit", 24)), 1), 60)
    posts = (
        MediaPost.query.filter(MediaPost.user_id == user.id, MediaPost.is_public.is_(True))
        .order_by(MediaPost.created_at.desc())
        .limit(limit)
        .all()
    )
    items = [
        {
            **post.to_dict(),
            "media_url": url_for("profile.uploaded_file", filename=post.file_path),
        }
        for post in posts
    ]
    return jsonify({"success": True, "items": items})
