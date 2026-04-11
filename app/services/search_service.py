from __future__ import annotations

import mimetypes
import re
import threading
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode

import requests
from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.utils import secure_filename


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}
PREVIEW_BYTES = 4096
IMAGE_HEADER_BYTES = 32
UPLOAD_TOKEN_SALT = "shadowseek-reverse-image"
_thread_local = threading.local()


@dataclass(frozen=True)
class PlatformDefinition:
    slug: str
    name: str
    category: str
    profile_url: str
    not_found_markers: tuple[str, ...] = ()


@dataclass(frozen=True)
class UsernameVariation:
    username: str
    score: int
    reason: str


@dataclass(frozen=True)
class SearchPayload:
    username: str
    real_name: str
    clan_name: str
    age: str
    postal_code: str
    deep_search: bool
    platforms: tuple[str, ...]


class SearchValidationError(ValueError):
    def __init__(self, errors):
        super().__init__("Die Suchanfrage ist ungueltig.")
        self.errors = errors


PLATFORMS = (
    PlatformDefinition(
        slug="instagram",
        name="Instagram",
        category="social",
        profile_url="https://www.instagram.com/{username}/",
        not_found_markers=("page isn't available", "sorry, this page isn't available"),
    ),
    PlatformDefinition(
        slug="tiktok",
        name="TikTok",
        category="social",
        profile_url="https://www.tiktok.com/@{username}",
        not_found_markers=("couldn't find this account",),
    ),
    PlatformDefinition(
        slug="x",
        name="Twitter/X",
        category="social",
        profile_url="https://x.com/{username}",
        not_found_markers=("this account doesn’t exist", "this account doesn't exist"),
    ),
    PlatformDefinition(
        slug="youtube",
        name="YouTube",
        category="video",
        profile_url="https://www.youtube.com/@{username}",
        not_found_markers=("this page isn't available",),
    ),
    PlatformDefinition(
        slug="twitch",
        name="Twitch",
        category="streaming",
        profile_url="https://www.twitch.tv/{username}",
        not_found_markers=("sorry. unless you've got a time machine",),
    ),
    PlatformDefinition(
        slug="reddit",
        name="Reddit",
        category="community",
        profile_url="https://www.reddit.com/user/{username}/",
        not_found_markers=("nobody on reddit goes by that name",),
    ),
    PlatformDefinition(
        slug="telegram",
        name="Telegram",
        category="messaging",
        profile_url="https://t.me/{username}",
    ),
    PlatformDefinition(
        slug="onlyfans",
        name="OnlyFans",
        category="subscription",
        profile_url="https://onlyfans.com/{username}",
        not_found_markers=("page not found", "error code 404"),
    ),
    PlatformDefinition(
        slug="github",
        name="GitHub",
        category="developer",
        profile_url="https://github.com/{username}",
        not_found_markers=("not found",),
    ),
)
PLATFORM_INDEX = {platform.slug: platform for platform in PLATFORMS}


def build_search_payload(form):
    errors = {}
    username = normalize_handle(form.get("username", ""))
    real_name = form.get("real_name", "").strip()
    clan_name = form.get("clan_name", "").strip()
    age = re.sub(r"\D", "", form.get("age", ""))
    postal_code = re.sub(r"[^A-Za-z0-9]", "", form.get("postal_code", "")).upper()
    deep_search = str(form.get("deep_search", "")).lower() in {"1", "true", "on", "yes"}
    selected_platforms = tuple(
        slug for slug in dict.fromkeys(form.getlist("platforms")) if slug in PLATFORM_INDEX
    )

    if not username or len(username) < 2:
        errors["username"] = "Bitte mindestens einen validen Username angeben."
    if age and not 1 <= int(age) <= 120:
        errors["age"] = "Das Alter muss zwischen 1 und 120 liegen."
    if postal_code and not 3 <= len(postal_code) <= 10:
        errors["postal_code"] = "Die Postleitzahl muss 3 bis 10 Zeichen haben."

    if errors:
        raise SearchValidationError(errors)

    return SearchPayload(
        username=username,
        real_name=real_name,
        clan_name=clan_name,
        age=age,
        postal_code=postal_code,
        deep_search=deep_search,
        platforms=selected_platforms or tuple(PLATFORM_INDEX),
    )


def generate_username_variations(payload):
    variants = {}
    limit = 10 if payload.deep_search else 8
    base_username = payload.username
    compact_username = re.sub(r"[._-]+", "", base_username)
    name_tokens = normalize_name_tokens(payload.real_name)
    clan = normalize_handle(payload.clan_name)

    def add(candidate, score, reason):
        normalized = normalize_handle(candidate)
        if not normalized or not 2 <= len(normalized) <= 32:
            return
        if normalized not in variants:
            variants[normalized] = UsernameVariation(normalized, score, reason)

    add(base_username, 100, "Direkter Username")
    if compact_username != base_username:
        add(compact_username, 97, "Normalisierter Username ohne Trenner")

    if name_tokens:
        first = name_tokens[0]
        add(first, 84, "Vorname als Handle")
        if len(name_tokens) >= 2:
            last = name_tokens[-1]
            add(f"{first}{last}", 92, "Vor- und Nachname kombiniert")
            add(f"{first}.{last}", 90, "Vorname.Nachname")
            add(f"{first}_{last}", 89, "Vorname_Nachname")
            add(f"{first[0]}{last}", 87, "Initiale plus Nachname")

    if clan:
        add(clan, 82, "Clanname als Handle")
        add(f"{clan}{base_username}", 88, "Clan plus Username")
        add(f"{clan}.{base_username}", 86, "Clan.Username")
        add(f"{base_username}{clan}", 84, "Username plus Clan")

    if payload.age:
        add(f"{base_username}{payload.age}", 83, "Username plus Alter")

    if payload.postal_code:
        add(f"{base_username}{payload.postal_code.lower()}", 81, "Username plus Postleitzahl")

    if payload.deep_search:
        if name_tokens:
            add(f"{base_username}_{name_tokens[0]}", 80, "Username plus Vorname")
        if clan and name_tokens:
            add(f"{clan}{name_tokens[0]}", 79, "Clan plus Vorname")
        if len(name_tokens) >= 2:
            first = name_tokens[0]
            last = name_tokens[-1]
            add(f"{first}{last}{payload.age}", 78, "Name plus Alter")
            add(f"{first}-{last}", 77, "Vorname-Nachname")
        add(f"{base_username}.official", 76, "Official-Suffix")

    return list(variants.values())[:limit]


def execute_search(payload, request_base_url, image_file=None):
    username_variations = generate_username_variations(payload)
    profiles = discover_profiles(payload, username_variations)
    reverse_image_links = {}

    if image_file and image_file.filename:
        reverse_image_links = create_reverse_image_links(image_file, request_base_url)

    return {
        "query": {
            "username": payload.username,
            "real_name": payload.real_name,
            "clan_name": payload.clan_name,
            "age": payload.age or None,
            "postal_code": payload.postal_code or None,
            "deep_search": payload.deep_search,
            "platforms": list(payload.platforms),
        },
        "username_variations": [
            {
                "username": variation.username,
                "score": variation.score,
                "reason": variation.reason,
            }
            for variation in username_variations
        ],
        "profiles": profiles,
        "reverse_image_links": reverse_image_links,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform_count": len(payload.platforms),
            "profile_count": len(profiles),
            "ai_reranking_applied": False,
        },
    }


def discover_profiles(payload, username_variations):
    platforms = [PLATFORM_INDEX[slug] for slug in payload.platforms]
    timeout = current_app.config["SEARCH_REQUEST_TIMEOUT"]
    max_workers = min(current_app.config["SEARCH_MAX_WORKERS"], len(platforms)) or 1
    hits = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(
                scan_platform,
                platform,
                username_variations,
                timeout,
                payload.deep_search,
            ): platform.slug
            for platform in platforms
        }
        for future in as_completed(future_map):
            hits.extend(future.result())

    return sorted(hits, key=lambda item: item["match_score"], reverse=True)


def scan_platform(platform, username_variations, timeout, deep_search):
    probe_limit = min(len(username_variations), 8 if deep_search else 4)
    result_limit = 2 if deep_search else 1
    results = []

    for variation in username_variations[:probe_limit]:
        profile = probe_profile(platform, variation, timeout)
        if profile:
            results.append(profile)
            if len(results) >= result_limit:
                break

    return results


def probe_profile(platform, variation, timeout):
    profile_url = platform.profile_url.format(username=quote(variation.username, safe="._-"))
    response = None

    try:
        response = get_http_session().get(
            profile_url,
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        status_code = response.status_code
        if status_code in {401, 403, 404, 410, 429} or status_code >= 500:
            return None

        preview = read_response_preview(response)
        final_url = response.url.lower()
        lower_username = variation.username.lower()

        if any(
            marker in final_url or marker in preview for marker in platform.not_found_markers
        ):
            return None

        verification = "confirmed"
        score = variation.score

        if lower_username not in final_url and lower_username not in preview:
            score -= 7
            verification = "likely"

        if any(token in final_url for token in ("/login", "/signup", "/auth")):
            score -= 5
            verification = "likely"

        return {
            "platform": platform.name,
            "platform_slug": platform.slug,
            "category": platform.category,
            "username": variation.username,
            "profile_url": response.url,
            "match_score": max(score, 50),
            "verification": verification,
            "match_reason": variation.reason,
            "http_status": status_code,
        }
    except requests.RequestException:
        return None
    finally:
        if response is not None:
            response.close()


def create_reverse_image_links(image_file, request_base_url):
    image_path, mime_type = save_uploaded_image(image_file)
    serializer = get_upload_serializer()
    token = serializer.dumps({"filename": image_path.name, "mime_type": mime_type})
    public_base_url = get_public_base_url(request_base_url)
    asset_url = f"{public_base_url}{url_for('search.reverse_image_asset', token=token)}"
    encoded_asset_url = urlencode({"url": asset_url})

    return {
        "asset_url": asset_url,
        "google_lens": f"https://lens.google.com/uploadbyurl?{encoded_asset_url}",
        "tineye": f"https://tineye.com/search?{encoded_asset_url}",
        "yandex": (
            "https://yandex.com/images/search?"
            f"rpt=imageview&{encoded_asset_url}"
        ),
    }


def save_uploaded_image(image_file):
    upload_directory = Path(current_app.config["UPLOAD_DIRECTORY"])
    purge_expired_uploads(upload_directory)

    try:
        header = image_file.stream.read(IMAGE_HEADER_BYTES)
        image_file.stream.seek(0)
        extension, mime_type = detect_image_type(header)

        if not extension:
            raise SearchValidationError(
                {"image": "Es werden nur JPG, PNG, GIF oder WEBP unterstuetzt."}
            )

        filename = secure_filename(image_file.filename or "")
        stored_name = f"{uuid.uuid4().hex}{extension}"
        stored_path = upload_directory / stored_name
        image_file.save(stored_path)

        if not stored_path.exists() or stored_path.stat().st_size == 0:
            raise SearchValidationError(
                {"image": "Der Bild-Upload konnte nicht gespeichert werden."}
            )

        if filename:
            mimetypes.add_type(mime_type, extension)

        return stored_path, mime_type
    finally:
        image_file.close()


def resolve_uploaded_image(token):
    try:
        payload = get_upload_serializer().loads(
            token,
            max_age=current_app.config["REVERSE_IMAGE_MAX_AGE"],
        )
    except (BadSignature, SignatureExpired):
        raise SearchValidationError({"image": "Der Reverse-Image-Link ist abgelaufen."})

    upload_directory = Path(current_app.config["UPLOAD_DIRECTORY"]).resolve()
    filename = secure_filename(payload["filename"])
    image_path = (upload_directory / filename).resolve()

    if upload_directory not in image_path.parents or not image_path.exists():
        raise SearchValidationError({"image": "Die angeforderte Bilddatei wurde nicht gefunden."})

    mime_type = payload.get("mime_type") or mimetypes.guess_type(image_path.name)[0]
    return image_path, mime_type or "application/octet-stream"


def purge_expired_uploads(upload_directory):
    max_age = current_app.config["REVERSE_IMAGE_MAX_AGE"] * 2
    cutoff = datetime.now(timezone.utc).timestamp() - max_age

    for file_path in upload_directory.glob("*"):
        if not file_path.is_file():
            continue
        if file_path.stat().st_mtime < cutoff:
            file_path.unlink(missing_ok=True)


def get_upload_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=UPLOAD_TOKEN_SALT)


def get_public_base_url(request_base_url):
    configured_base_url = current_app.config.get("PUBLIC_BASE_URL")
    if configured_base_url:
        return configured_base_url.rstrip("/")
    return request_base_url.rstrip("/")


def get_http_session():
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        _thread_local.session = session
    return session


def read_response_preview(response):
    content = bytearray()
    for chunk in response.iter_content(chunk_size=1024):
        if not chunk:
            continue
        content.extend(chunk)
        if len(content) >= PREVIEW_BYTES:
            break
    return content.decode(response.encoding or "utf-8", errors="ignore").lower()


def normalize_handle(value):
    normalized = normalize_ascii(value).lower()
    normalized = normalized.replace(" ", "")
    normalized = re.sub(r"[^a-z0-9._-]", "", normalized)
    return normalized.strip("._-")


def normalize_name_tokens(value):
    normalized = normalize_ascii(value).lower()
    return re.findall(r"[a-z0-9]+", normalized)


def normalize_ascii(value):
    value = value or ""
    return (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
    )


def detect_image_type(header):
    if header.startswith(b"\xFF\xD8\xFF"):
        return ".jpg", "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1A\n"):
        return ".png", "image/png"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return ".gif", "image/gif"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp", "image/webp"
    return None, None
