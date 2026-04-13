from datetime import datetime
import json
import os

from bs4 import BeautifulSoup

SCRIPT_IDS = ["SIGI_STATE", "__UNIVERSAL_DATA_FOR_REHYDRATION__", "_STATE"]


def _load_state_data(soup):
    script_tag = None
    for script_id in SCRIPT_IDS:
        script_tag = soup.find("script", {"id": script_id})
        if script_tag:
            break

    if not script_tag:
        raise ExtractorError("NO_STATE_SCRIPT", "Kein TikTok-State-Script gefunden.")

    payload = script_tag.string or script_tag.get_text(strip=True)
    try:
        return json.loads(payload)
    except Exception as error:
        raise ExtractorError("INVALID_STATE_JSON", f"JSON-Parsing fehlgeschlagen: {error}") from error


def _write_debug_html(html, debug_dir):
    if not debug_dir:
        return

    os.makedirs(debug_dir, exist_ok=True)
    with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as handle:
        handle.write(html)


def extract_video_data(html, debug_dir=None, logger=None):
    soup = BeautifulSoup(html, "html.parser")

    try:
        data = _load_state_data(soup)
    except ExtractorError as error:
        if logger:
            logger.warning("[extract_video_data] %s", error.message)
        _write_debug_html(html, debug_dir)
        raise

    item_module = data.get("ItemModule") or data.get("itemModule")
    if not isinstance(item_module, dict) or not item_module:
        raise ExtractorError("VIDEO_DATA_EMPTY", "ItemModule ist leer oder fehlt im TikTok-State.")

    video_data = next(iter(item_module.values()), {})
    if not video_data:
        raise ExtractorError("VIDEO_DATA_EMPTY", "Video-Daten im ItemModule sind leer.")

    stats = video_data.get("stats", {}) if isinstance(video_data.get("stats"), dict) else {}
    return {
        "video_id": video_data.get("id"),
        "description": video_data.get("desc"),
        "author_username": video_data.get("author"),
        "views": stats.get("playCount"),
        "likes": stats.get("diggCount"),
        "comments_count": stats.get("commentCount"),
        "shares": stats.get("shareCount"),
    }


def extract_profile_data(html, debug_dir=None, logger=None):
    soup = BeautifulSoup(html, "html.parser")

    try:
        data = _load_state_data(soup)
    except ExtractorError as error:
        if logger:
            logger.warning("[extract_profile_data] %s", error.message)
        _write_debug_html(html, debug_dir)
        raise

    user_module = data.get("UserModule") if isinstance(data.get("UserModule"), dict) else {}
    users_map = user_module.get("users") if isinstance(user_module.get("users"), dict) else {}
    stats_map = user_module.get("stats") if isinstance(user_module.get("stats"), dict) else {}

    username = None
    profile = {}
    if users_map:
        username, profile = next(iter(users_map.items()))
    elif isinstance(data.get("UserPage"), dict):
        user_info = data["UserPage"].get("userInfo") if isinstance(data["UserPage"].get("userInfo"), dict) else {}
        user_data = user_info.get("user") if isinstance(user_info.get("user"), dict) else {}
        username = user_data.get("uniqueId")
        profile = user_data

    if not username and isinstance(profile, dict):
        username = profile.get("uniqueId") or profile.get("unique_id")

    stats = stats_map.get(username, {}) if username and isinstance(stats_map.get(username), dict) else {}
    if not stats and isinstance(data.get("UserPage"), dict):
        user_info = data["UserPage"].get("userInfo") if isinstance(data["UserPage"].get("userInfo"), dict) else {}
        stats = user_info.get("stats") if isinstance(user_info.get("stats"), dict) else {}

    return {
        "video_id": None,
        "description": profile.get("signature") if isinstance(profile, dict) else None,
        "author_username": username,
        "author_nickname": profile.get("nickname") if isinstance(profile, dict) else None,
        "followers": stats.get("followerCount"),
        "following": stats.get("followingCount"),
        "likes_total": stats.get("heartCount") or stats.get("heart"),
        "videos_total": stats.get("videoCount"),
        "is_private": profile.get("privateAccount") if isinstance(profile, dict) else None,
        "scraped_profile_at": datetime.utcnow().isoformat(),
    }


class ExtractorError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
