from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

from flask import current_app, url_for


_URL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)


def _is_http_url(value: str) -> bool:
    return bool(value and _URL_PATTERN.match(value.strip()))


def _is_plausible_url(value: str) -> bool:
    """Best-effort check to avoid rendering obviously broken URLs."""
    if not _is_http_url(value):
        return False
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return bool(parsed.scheme and parsed.netloc)


def _uploads_root() -> Path:
    return Path(current_app.config["UPLOAD_DIRECTORY"]).resolve()


def _static_root() -> Path:
    # Flask sets this to the folder that backs `url_for('static', ...)`.
    return Path(current_app.static_folder).resolve()


def _file_exists(path: Path) -> bool:
    try:
        return path.exists() and path.is_file()
    except OSError:
        return False


def resolve_user_avatar_url(user) -> str:
    """Return a safe avatar URL for templates (supports live + missing files)."""
    return _resolve_user_image_url(
        stored_value=(getattr(user, "avatar", None) or "").strip(),
        kind="avatar",
        default_static_filename="images/default-avatar.png",
    )


def resolve_user_banner_url(user) -> str:
    """Return a safe banner URL for templates (supports live + missing files)."""
    return _resolve_user_image_url(
        stored_value=(getattr(user, "banner", None) or "").strip(),
        kind="banner",
        default_static_filename="images/default-banner.jpg",
    )


def _resolve_user_image_url(*, stored_value: str, kind: str, default_static_filename: str) -> str:
    if stored_value and _is_plausible_url(stored_value):
        return stored_value

    # New storage format: relative path inside UPLOAD_DIRECTORY, e.g. "avatars/user_1_avatar_....png"
    if stored_value and not stored_value.startswith(("img/", "images/")):
        candidate = (_uploads_root() / stored_value).resolve()
        if str(candidate).startswith(str(_uploads_root())) and _file_exists(candidate):
            return url_for("profile.uploaded_file", filename=stored_value)

    # Legacy storage format: relative path inside static/, e.g. "img/avatars/..."
    if stored_value and stored_value.startswith(("img/", "images/")):
        candidate = (_static_root() / stored_value).resolve()
        if str(candidate).startswith(str(_static_root())) and _file_exists(candidate):
            return url_for("static", filename=stored_value)

    current_app.logger.debug(
        "media_resolve_fallback kind=%s stored_value=%r upload_dir=%s",
        kind,
        stored_value,
        current_app.config.get("UPLOAD_DIRECTORY"),
    )
    return url_for("static", filename=default_static_filename)

