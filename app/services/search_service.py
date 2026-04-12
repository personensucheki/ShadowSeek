from __future__ import annotations

import mimetypes
import re
import threading
import unicodedata
import uuid
import xml.etree.ElementTree as ET
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timezone
from html import unescape
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

IMAGE_HEADER_BYTES = 32
UPLOAD_TOKEN_SALT = "shadowseek-reverse-image"

_thread_local = threading.local()


@dataclass(frozen=True)
class PlatformDefinition:
    slug: str
    name: str
    category: str
    profile_url: str
    domains: tuple[str, ...]
    excluded_segments: tuple[str, ...] = ()


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
        super().__init__("The search request is invalid.")
        self.errors = errors


PLATFORM_GROUPS = {
    "social": [
        {
            "slug": "instagram",
            "name": "Instagram",
            "url_pattern": "https://www.instagram.com/{username}/",
            "domains": ("instagram.com",),
            "excluded_segments": ("p", "reel", "reels", "stories", "explore", "accounts"),
        },
        {
            "slug": "tiktok",
            "name": "TikTok",
            "url_pattern": "https://www.tiktok.com/@{username}",
            "domains": ("tiktok.com",),
            "excluded_segments": ("discover", "tag", "search", "music"),
        },
        {
            "slug": "x",
            "name": "Twitter/X",
            "url_pattern": "https://x.com/{username}",
            "domains": ("x.com", "twitter.com"),
            "excluded_segments": ("home", "explore", "search", "i", "hashtag", "messages", "compose"),
        },
        {
            "slug": "youtube",
            "name": "YouTube",
            "url_pattern": "https://www.youtube.com/@{username}",
            "domains": ("youtube.com",),
            "excluded_segments": ("watch", "results", "playlist", "shorts", "feed"),
        },
        {
            "slug": "reddit",
            "name": "Reddit",
            "url_pattern": "https://www.reddit.com/user/{username}/",
            "domains": ("reddit.com",),
            "excluded_segments": ("r", "search", "media", "topics"),
        },
        {
            "slug": "facebook",
            "name": "Facebook",
            "url_pattern": "https://www.facebook.com/{username}",
            "domains": ("facebook.com",),
            "excluded_segments": ("watch", "marketplace", "groups", "events"),
        },
        {
            "slug": "snapchat",
            "name": "Snapchat",
            "url_pattern": "https://www.snapchat.com/add/{username}",
            "domains": ("snapchat.com",),
            "excluded_segments": ("discover", "spotlight", "lenses"),
        },
        {
            "slug": "pinterest",
            "name": "Pinterest",
            "url_pattern": "https://www.pinterest.com/{username}/",
            "domains": ("pinterest.com",),
            "excluded_segments": ("pin", "ideas", "search"),
        },
        {
            "slug": "tumblr",
            "name": "Tumblr",
            "url_pattern": "https://{username}.tumblr.com",
            "domains": ("tumblr.com",),
            "excluded_segments": ("explore", "search", "dashboard"),
        },
    ],
    "gaming": [
        {
            "slug": "twitch",
            "name": "Twitch",
            "url_pattern": "https://www.twitch.tv/{username}",
            "domains": ("twitch.tv",),
            "excluded_segments": ("directory", "downloads", "jobs", "store", "settings"),
        },
        {
            "slug": "kick",
            "name": "Kick",
            "url_pattern": "https://kick.com/{username}",
            "domains": ("kick.com",),
            "excluded_segments": ("browse", "categories", "following"),
        },
        {
            "slug": "steam",
            "name": "Steam",
            "url_pattern": "https://steamcommunity.com/id/{username}",
            "domains": ("steamcommunity.com",),
            "excluded_segments": ("app", "groups", "market", "workshop", "search"),
        },
        {
            "slug": "github",
            "name": "GitHub",
            "url_pattern": "https://github.com/{username}",
            "domains": ("github.com",),
            "excluded_segments": ("topics", "explore", "features", "marketplace", "orgs", "settings"),
        },
    ],
    "community": [
        {
            "slug": "telegram",
            "name": "Telegram",
            "url_pattern": "https://t.me/{username}",
            "domains": ("t.me", "telegram.me"),
            "excluded_segments": ("share", "addstickers", "s", "blog"),
        },
        {
            "slug": "discord",
            "name": "Discord",
            "url_pattern": "https://discord.gg/{username}",
            "domains": ("discord.gg", "discord.com"),
            "excluded_segments": ("app", "download", "channels"),
        },
        {
            "slug": "vk",
            "name": "VK",
            "url_pattern": "https://vk.com/{username}",
            "domains": ("vk.com",),
            "excluded_segments": ("feed", "music", "video"),
        },
    ],
}


def _build_platform_definitions() -> tuple[PlatformDefinition, ...]:
    definitions: list[PlatformDefinition] = []
    for category, platforms in PLATFORM_GROUPS.items():
        for platform in platforms:
            definitions.append(
                PlatformDefinition(
                    slug=platform["slug"],
                    name=platform["name"],
                    category=category,
                    profile_url=platform["url_pattern"],
                    domains=tuple(platform["domains"]),
                    excluded_segments=tuple(platform.get("excluded_segments", ())),
                )
            )
    return tuple(definitions)


PLATFORMS = _build_platform_definitions()
PLATFORM_INDEX = {platform.slug: platform for platform in PLATFORMS}


def list_platform_cards():
    cards = [
        {
            "slug": platform.slug,
            "name": platform.name,
            "category": platform.category,
            "url_pattern": platform.profile_url,
        }
        for platform in PLATFORMS
    ]
    return sorted(cards, key=lambda item: (item["category"], item["name"]))


def normalize_ascii(value):
    value = value or ""
    return (
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode("ascii")
        .strip()
    )


def normalize_handle(value):
    normalized = normalize_ascii(value).lower()
    normalized = normalized.replace(" ", "")
    normalized = re.sub(r"[^a-z0-9._-]", "", normalized)
    return normalized.strip("._-")


def normalize_name_tokens(value):
    normalized = normalize_ascii(value).lower()
    return re.findall(r"[a-z0-9]+", normalized)


def collapse_whitespace(value):
    return re.sub(r"\s+", " ", value or "").strip()


def build_search_payload(form):
    errors = {}
    username = normalize_handle(form.get("username", ""))
    real_name = collapse_whitespace(form.get("real_name", ""))
    clan_name = collapse_whitespace(form.get("clan_name", ""))
    age = re.sub(r"\D", "", form.get("age", ""))
    postal_code = re.sub(r"[^A-Za-z0-9]", "", form.get("postal_code", "")).upper()
    deep_search = str(form.get("deep_search", "")).lower() in {"1", "true", "on", "yes"}
    getlist = getattr(form, "getlist", None)
    raw_platforms = getlist("platforms") if callable(getlist) else form.get("platforms", [])
    if isinstance(raw_platforms, str):
        raw_platforms = [raw_platforms]
    selected_platforms = tuple(
        slug for slug in dict.fromkeys(raw_platforms or []) if slug in PLATFORM_INDEX
    )

    if not username or len(username) < 2:
            errors["username"] = "Bitte einen gueltigen Username angeben."
    if len(username) > 32:
        errors["username"] = "Der Username darf nicht laenger als 32 Zeichen sein."
    if age and not 1 <= int(age) <= 120:
        errors["age"] = "Das Alter muss zwischen 1 und 120 liegen."
    if postal_code and not 3 <= len(postal_code) <= 10:
        errors["postal_code"] = "Die Postleitzahl muss zwischen 3 und 10 Zeichen haben."

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
    variants: "OrderedDict[str, UsernameVariation]" = OrderedDict()

    def add(candidate, score, reason):
        normalized = normalize_handle(candidate)
        if not normalized or not 2 <= len(normalized) <= 32:
            return
        if normalized not in variants:
            variants[normalized] = UsernameVariation(normalized, int(score), reason)

    base_username = payload.username
    compact_username = re.sub(r"[._-]+", "", base_username)

    add(base_username, 100, "Exact username")
    if compact_username != base_username:
        add(compact_username, 96, "Normalized username without separators")

    add(f"{base_username}official", 88, "Username plus official suffix")
    add(f"{base_username}tv", 86, "Username plus tv suffix")
    add(f"{base_username}live", 85, "Username plus live suffix")

    if payload.deep_search:
        add(f"{base_username}_official", 84, "Username underscore official")
        add(f"{base_username}.official", 82, "Username dot official")
        add(f"{base_username}app", 80, "Username plus app suffix")

    return list(variants.values())[:10]


def _confidence_from_score(score):
    if score >= 90:
        return "high"
    if score >= 75:
        return "medium"
    return "low"


def _platform_profile_url(platform, username):
    return platform.profile_url.format(username=quote(username, safe="._-"))


def _build_candidate_result(platform, variation, *, deep_search=False):
    score = variation.score
    verification = "candidate"
    if variation.username == normalize_handle(variation.username):
        score = min(score, 100)
    if deep_search and score < 90:
        score = min(score + 2, 92)

    return {
        "platform": platform.name,
        "platform_slug": platform.slug,
        "category": platform.category,
        "username": variation.username,
        "profile_url": _platform_profile_url(platform, variation.username),
        "url": _platform_profile_url(platform, variation.username),
        "match_score": score,
        "verification": verification,
        "confidence": _confidence_from_score(score),
        "match_reason": f"{variation.reason} (lokaler Kandidatenlink ohne automatische Plattformpruefung)",
        "source": "local",
        "title": f"Oeffentlicher Link fuer {platform.name}",
        "snippet": "Lokaler Kandidatenlink zur manuellen Pruefung.",
    }


def dedupe_and_limit_profiles(profiles, deep_search):
    per_platform_limit = 2 if deep_search else 1
    deduped = {}

    for profile in profiles:
        key = (profile["platform_slug"], profile["profile_url"])
        existing = deduped.get(key)
        if not existing or profile["match_score"] > existing["match_score"]:
            deduped[key] = profile

    grouped = {}
    for profile in deduped.values():
        grouped.setdefault(profile["platform_slug"], []).append(profile)

    limited = []
    for items in grouped.values():
        limited.extend(
            sorted(items, key=lambda item: item["match_score"], reverse=True)[:per_platform_limit]
        )

    return sorted(limited, key=lambda item: item["match_score"], reverse=True)


def execute_search(payload, request_base_url, image_file=None):
    username_variations = generate_username_variations(payload)
    selected_platforms = [PLATFORM_INDEX[slug] for slug in payload.platforms if slug in PLATFORM_INDEX]
    if not selected_platforms:
        selected_platforms = list(PLATFORMS)

    primary_variation = username_variations[0] if username_variations else UsernameVariation(payload.username, 100, "Exact username")
    profiles = []

    for platform in selected_platforms:
        profiles.append(_build_candidate_result(platform, primary_variation, deep_search=payload.deep_search))
        if payload.deep_search and len(username_variations) > 1:
            profiles.append(
                _build_candidate_result(
                    platform,
                    username_variations[1],
                    deep_search=payload.deep_search,
                )
            )

    profiles = dedupe_and_limit_profiles(profiles, payload.deep_search)
    reverse_image_links = {}
    if image_file and getattr(image_file, "filename", ""):
        reverse_image_links = create_reverse_image_links(image_file, request_base_url)

    return {
        "query": {
            "username": payload.username,
            "deep_search": payload.deep_search,
            "platforms": list(payload.platforms),
            "safe_mode": True,
        },
        "username_variations": [
            {"username": item.username, "score": item.score, "reason": item.reason}
            for item in username_variations
        ],
        "profiles": [
            {
                **profile,
                "confidence": profile.get("confidence") or _confidence_from_score(profile["match_score"]),
            }
            for profile in profiles
        ],
        "reverse_image_search": reverse_image_links,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform_count": len(payload.platforms),
            "profile_count": len(profiles),
            "ai_reranking_applied": False,
            "serper_used": False,
            "serper_queries": 0,
            "search_engine_used": False,
            "search_engine_provider": None,
            "search_engine_queries": 0,
            "safe_mode": True,
        },
    }


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
        "yandex": f"https://yandex.com/images/search?rpt=imageview&{encoded_asset_url}",
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
                {"image": "Only JPG, PNG, GIF, or WEBP images are supported."}
            )

        stored_name = f"{uuid.uuid4().hex}{extension}"
        stored_path = upload_directory / stored_name
        image_file.save(stored_path)

        if not stored_path.exists() or stored_path.stat().st_size == 0:
            raise SearchValidationError({"image": "The image upload could not be saved."})

        mimetypes.add_type(mime_type, extension)
        return stored_path, mime_type
    finally:
        try:
            image_file.close()
        except Exception:
            pass


def resolve_uploaded_image(token):
    try:
        payload = get_upload_serializer().loads(
            token,
            max_age=current_app.config["REVERSE_IMAGE_MAX_AGE"],
        )
    except (BadSignature, SignatureExpired) as exc:
        raise SearchValidationError({"image": "The reverse image link has expired."}) from exc

    upload_directory = Path(current_app.config["UPLOAD_DIRECTORY"]).resolve()
    filename = secure_filename(payload["filename"])
    image_path = (upload_directory / filename).resolve()

    if upload_directory not in image_path.parents or not image_path.exists():
        raise SearchValidationError({"image": "The requested image file was not found."})

    mime_type = payload.get("mime_type") or mimetypes.guess_type(image_path.name)[0]
    return image_path, mime_type or "application/octet-stream"


def purge_expired_uploads(upload_directory):
    max_age = int(current_app.config["REVERSE_IMAGE_MAX_AGE"]) * 2
    cutoff = datetime.now(timezone.utc).timestamp() - max_age

    for file_path in upload_directory.glob("*"):
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
            file_path.unlink(missing_ok=True)


def get_upload_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt=UPLOAD_TOKEN_SALT)


def get_public_base_url(request_base_url):
    configured_base_url = current_app.config.get("PUBLIC_BASE_URL")
    if configured_base_url:
        return configured_base_url.rstrip("/")
    return request_base_url.rstrip("/")


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


def get_http_session():
    session = getattr(_thread_local, "session", None)
    if session is None:
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        _thread_local.session = session
    return session


def parse_bing_rss_feed(xml_text, limit=8):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {"organic": []}

    items = []
    for item in root.findall(".//item"):
        title = collapse_whitespace(unescape(item.findtext("title", default="")))
        link = collapse_whitespace(unescape(item.findtext("link", default="")))
        description = collapse_whitespace(unescape(item.findtext("description", default="")))
        if not title or not link:
            continue
        items.append({"title": title, "link": link, "snippet": description})
        if len(items) >= limit:
            break

    return {"organic": items}


def run_serper_query(query, config):
    api_key = (config or {}).get("api_key")
    api_url = (config or {}).get("api_url")
    if not api_key or not api_url:
        raise RuntimeError("Serper is not configured.")

    payload = {
        "q": query,
        "gl": (config or {}).get("gl", "de"),
        "hl": (config or {}).get("hl", "de"),
        "num": int((config or {}).get("num", 8)),
    }
    response = get_http_session().post(
        api_url,
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json=payload,
        timeout=float((config or {}).get("timeout", 6.0)),
    )
    response.raise_for_status()
    return response.json()


def has_serper_api_key():
    return bool(current_app.config.get("SERPER_API_KEY"))


def has_public_search_fallback():
    return bool(current_app.config.get("PUBLIC_SEARCH_FALLBACK_ENABLED"))


def should_ai_rerank(payload, profiles):
    return False


def collect_serper_profiles(*_args, **_kwargs):
    return [], {"used": False, "queries": 0, "provider": None}


def collect_bing_profiles(*_args, **_kwargs):
    return [], {"used": False, "queries": 0, "provider": None}


def discover_profiles(*_args, **_kwargs):
    return []


def scan_platform(*_args, **_kwargs):
    return []


def probe_profile(*_args, **_kwargs):
    return None


def rerank_profiles_with_openai(payload, username_variations, profiles):
    return profiles, False


def normalize_result_url(url):
    if not url:
        return None
    return str(url).strip()


def resolve_platform_from_url(url):
    if not url:
        return None
    lower_url = str(url).lower()
    for platform in PLATFORMS:
        if any(domain in lower_url for domain in platform.domains):
            return platform
    return None


def is_profile_like_url(platform, url):
    if not platform or not url:
        return False
    return platform.slug in str(url).lower()


def extract_username_from_url(platform, url):
    if not platform or not url:
        return None
    return normalize_handle(str(url).rstrip("/").split("/")[-1].lstrip("@"))


def select_best_variation(username_variations, extracted_username, title, snippet, url):
    if not username_variations:
        return None
    extracted = normalize_handle(extracted_username)
    for variation in username_variations:
        if variation.username == extracted:
            return variation
    return username_variations[0]


def generate_search_summary(results: list, meta: dict) -> dict:
    if not results:
        return {
            "strongest_platform": None,
            "best_result": None,
            "confidence_distribution": {"high": 0, "medium": 0, "low": 0},
            "used_variants": meta.get("used_variants", []),
            "used_providers": meta.get("providers", []),
            "warnings": ["No results available."],
        }

    best_result = results[0]
    strongest_platform = best_result.get("platform")
    conf_dist = {"high": 0, "medium": 0, "low": 0}
    for result in results:
        confidence = result.get("confidence", "low")
        if confidence in conf_dist:
            conf_dist[confidence] += 1

    warnings = []
    if conf_dist["high"] == 0:
        warnings.append("No strong results found.")
    if conf_dist["medium"] == 0 and conf_dist["high"] == 0:
        warnings.append("Only weak results found.")

    return {
        "strongest_platform": strongest_platform,
        "best_result": best_result,
        "confidence_distribution": conf_dist,
        "used_variants": meta.get("used_variants", []),
        "used_providers": meta.get("providers", []),
        "warnings": warnings,
    }
