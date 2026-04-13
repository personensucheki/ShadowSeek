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
    public_sources: bool
    ai_rerank: bool
    secure_mode: bool
    precision_mode: bool
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
    "adult": [
        {
            "slug": "onlyfans",
            "name": "OnlyFans",
            "url_pattern": "https://onlyfans.com/{username}",
            "domains": ("onlyfans.com",),
            "excluded_segments": ("login", "signup", "my", "terms", "privacy"),
        },
        {
            "slug": "fansly",
            "name": "Fansly",
            "url_pattern": "https://fansly.com/{username}",
            "domains": ("fansly.com",),
            "excluded_segments": ("auth", "terms", "privacy"),
        },
    ],
    "porn": [
        {
            "slug": "pornhub",
            "name": "Pornhub",
            "url_pattern": "https://www.pornhub.com/users/{username}",
            "domains": ("pornhub.com",),
            "excluded_segments": ("video", "view_video", "pornstar", "categories", "gifs", "playlists"),
        },
        {
            "slug": "xhamster",
            "name": "xHamster",
            "url_pattern": "https://xhamster.com/users/{username}",
            "domains": ("xhamster.com",),
            "excluded_segments": ("videos", "categories", "pornstars", "search"),
        },
        {
            "slug": "xnxx",
            "name": "XNXX",
            "url_pattern": "https://www.xnxx.com/profiles/{username}",
            "domains": ("xnxx.com",),
            "excluded_segments": ("video", "search", "tags", "pornstars"),
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
    public_sources = str(form.get("public_sources", "on")).lower() in {"1", "true", "on", "yes"}
    ai_rerank_raw = str(form.get("ai_rerank", "")).lower()
    ai_rerank = ai_rerank_raw in {"1", "true", "on", "yes"}
    if not ai_rerank_raw and deep_search:
        ai_rerank = True
    secure_mode = str(form.get("secure_mode", "")).lower() in {"1", "true", "on", "yes"}
    precision_mode = str(form.get("precision_mode", "")).lower() in {"1", "true", "on", "yes"}
    import logging
    getlist = getattr(form, "getlist", None)
    raw_platforms = getlist("platforms") if callable(getlist) else form.get("platforms", [])
    logging.warning("SEARCH_RAW_PLATFORM_INPUT=%r", raw_platforms)
    # Normalize platforms: handle single string, list, tuple, etc.
    if isinstance(raw_platforms, str):
        # Could be comma-separated or single value
        if "," in raw_platforms:
            raw_platforms = [p.strip().lower() for p in raw_platforms.split(",") if p.strip()]
        else:
            raw_platforms = [raw_platforms.strip().lower()] if raw_platforms.strip() else []
    elif isinstance(raw_platforms, (list, tuple)):
        # Lowercase and trim all entries
        raw_platforms = [str(p).strip().lower() for p in raw_platforms if str(p).strip()]
    else:
        raw_platforms = []
    logging.warning("SEARCH_PAYLOAD_PLATFORMS=%r", raw_platforms)
    selected_platforms = tuple(
        slug for slug in dict.fromkeys(raw_platforms or []) if slug in PLATFORM_INDEX
    )
    logging.warning("SEARCH_SELECTED_PLATFORMS=%r", selected_platforms)

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
        public_sources=public_sources,
        ai_rerank=ai_rerank,
        secure_mode=secure_mode,
        precision_mode=precision_mode,
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
    # Bound deepsearch to max 2 per platform, never more than 20 total
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

    return sorted(limited, key=lambda item: item["match_score"], reverse=True)[:20]


def execute_search(payload, request_base_url, image_file=None):
    username_variations = generate_username_variations(payload)
    selected_platforms = [PLATFORM_INDEX[slug] for slug in payload.platforms if slug in PLATFORM_INDEX]
    if not selected_platforms:
        selected_platforms = list(PLATFORMS)

    primary_variation = username_variations[0] if username_variations else UsernameVariation(payload.username, 100, "Exact username")
    profiles = []

    import logging
    for platform in selected_platforms:
        logging.warning("SEARCH_DISPATCH_DECISION: platform.slug=%r", platform.slug)
        if platform.slug == "tiktok":
            logging.warning("SEARCH_DISPATCH_TRACE: Attempting TikTok provider dispatch for username='%s'", payload.username)
            try:
                from app.providers.tiktok_provider import TikTokProvider
                provider = TikTokProvider()
                provider_result = provider.search_creator(
                    payload.username,
                    platform.slug,
                    getattr(payload, "real_name", None),
                    getattr(payload, "deep_search", False),
                )
                logging.warning("SEARCH_DISPATCH_TRACE: TikTok provider returned result: %s", bool(provider_result))
                if provider_result:
                    profiles.append({
                        "platform": platform.name,
                        "platform_slug": platform.slug,
                        "category": platform.category,
                        "username": payload.username,
                        "profile_url": f"https://www.tiktok.com/@{payload.username}",
                        "url": f"https://www.tiktok.com/@{payload.username}",
                        "match_score": 100,
                        "verification": "provider",
                        "confidence": "high",
                        "match_reason": "TikTok provider executed",
                        "source": "tiktok_provider",
                        "title": "TikTok Provider Result",
                        "snippet": str(provider_result),
                    })
                else:
                    logging.warning("SEARCH_DISPATCH_TRACE: TikTok provider returned no result.")
            except Exception as e:
                logging.error("SEARCH_DISPATCH_TRACE: TikTok provider dispatch failed: %s", e)
        else:
            profiles.append(_build_candidate_result(platform, primary_variation, deep_search=payload.deep_search))
            if payload.deep_search and len(username_variations) > 1:
                profiles.append(
                    _build_candidate_result(
                        platform,
                        username_variations[1],
                        deep_search=payload.deep_search,
                    )
                )

    serper_meta = {"used": False, "queries": 0, "provider": None}
    search_engine_meta = {"used": False, "queries": 0, "provider": None}

    # External search providers should only run when explicitly enabled via the UI
    # ("Oeffentliche Quellen"). Otherwise keep results local (candidate links only).
    if payload.public_sources:
        if has_serper_api_key():
            serper_profiles, serper_meta = collect_serper_profiles(
                payload, username_variations, selected_platforms
            )
            if serper_profiles:
                # When a search provider is available, return provider-backed results first.
                # Local candidate links remain useful as a fallback, but they should not overshadow real results.
                profiles = list(serper_profiles)
        else:
            discovered = discover_profiles(payload, username_variations, selected_platforms)
            if isinstance(discovered, tuple) and len(discovered) == 2:
                discovered_profiles, search_engine_meta = discovered
            else:
                discovered_profiles = discovered
            if discovered_profiles:
                profiles.extend(discovered_profiles)


    profiles = dedupe_and_limit_profiles(profiles, payload.deep_search)

    # --- AI reranker integration (optional, robust fallback) ---
    ai_reranked = False
    rerank_provider = None
    rerank_fallback_used = False
    reranked_profiles = profiles
    if getattr(payload, "ai_rerank", False):
        try:
            reranked_profiles, ai_reranked = rerank_profiles_with_openai(
                payload,
                username_variations,
                profiles,
            )
            rerank_provider = "openai" if ai_reranked else None
            rerank_fallback_used = not ai_reranked
        except Exception:
            rerank_fallback_used = True

    reverse_image_links = {}
    if image_file and getattr(image_file, "filename", ""):
        reverse_image_links = create_reverse_image_links(image_file, request_base_url)

    return {
        "query": {
            "username": payload.username,
            "deep_search": payload.deep_search,
            "platforms": list(payload.platforms),
            "public_sources": payload.public_sources,
            "ai_rerank": payload.ai_rerank,
            "secure_mode": payload.secure_mode,
            "precision_mode": payload.precision_mode,
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
            for profile in reranked_profiles
        ],
        "reverse_image_search": reverse_image_links,
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "platform_count": len(payload.platforms),
            "profile_count": len(reranked_profiles),
            "ai_reranked": ai_reranked,
            "ai_reranking_applied": ai_reranked,
            "rerank_provider": rerank_provider,
            "rerank_fallback_used": rerank_fallback_used,
            "serper_used": bool(serper_meta.get("used")),
            "serper_queries": int(serper_meta.get("queries") or 0),
            "search_engine_used": bool(search_engine_meta.get("used")),
            "search_engine_provider": search_engine_meta.get("provider"),
            "search_engine_queries": int(search_engine_meta.get("queries") or 0),
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
    import logging
    try:
        response = get_http_session().post(
            api_url,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=float((config or {}).get("timeout", 6.0)),
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.warning(f"[Serper] Provider call failed or timed out: {e}")
        return {"organic": []}


def has_serper_api_key():
    return bool(current_app.config.get("SERPER_API_KEY"))


def has_public_search_fallback():
    return bool(current_app.config.get("PUBLIC_SEARCH_FALLBACK_ENABLED"))


def should_ai_rerank(payload, profiles):
    if not payload or not getattr(payload, "deep_search", False):
        return False
    if not profiles:
        return False
    return bool(current_app.config.get("OPENAI_API_KEY"))

def _build_serper_query(username: str, platform: PlatformDefinition | None = None) -> str:
    username = normalize_handle(username)
    if not username:
        return ""
    if not platform:
        return f"\"{username}\" profile"
    domain = platform.domains[0] if platform.domains else ""
    if domain:
        if platform.slug == "tiktok":
            return f"site:{domain} \"@{username}\""
        return f"site:{domain} \"{username}\""
    return f"\"{username}\" {platform.name}"


def collect_serper_profiles(payload, username_variations, selected_platforms):
    if not has_serper_api_key():
        return [], {"used": False, "queries": 0, "provider": None}

    max_queries = 2 if payload.precision_mode else 4
    timeout = float(current_app.config.get("SEARCH_REQUEST_TIMEOUT", 3.5)) + 2
    num = int(current_app.config.get("SERPER_RESULTS_PER_QUERY", 8))

    queries: list[str] = []
    for variation in username_variations[:2]:
        queries.append(_build_serper_query(variation.username))
    if payload.deep_search and selected_platforms:
        for platform in selected_platforms[: min(3, len(selected_platforms))]:
            queries.append(_build_serper_query(username_variations[0].username, platform))

    queries = [q for q in queries if q]
    queries = list(dict.fromkeys(queries))[:max_queries]

    raw_results: list[dict] = []
    used_queries = 0
    import logging
    for q in queries:
        data = run_serper_query(
            q,
            {
                "api_url": current_app.config.get("SERPER_API_URL"),
                "api_key": current_app.config.get("SERPER_API_KEY"),
                "gl": current_app.config.get("SERPER_GL", "de"),
                "hl": current_app.config.get("SERPER_HL", "de"),
                "num": num,
                "timeout": timeout,
            },
        )
        organic = data.get("organic") or []
        if not organic:
            logging.info(f"[Serper] No organic results for query: {q}")
        for item in organic:
            link = normalize_result_url(item.get("link"))
            if not link:
                continue
            raw_results.append(
                {
                    "title": collapse_whitespace(item.get("title") or ""),
                    "link": link,
                    "snippet": collapse_whitespace(item.get("snippet") or ""),
                }
            )
        used_queries += 1

    profiles: list[dict] = []
    for platform in selected_platforms:
        for profile in scan_platform(payload, username_variations, platform, raw_results):
            profile.setdefault("source", "serper")
            profiles.append(profile)

    return profiles, {
        "used": bool(used_queries),
        "queries": used_queries,
        "provider": "serper" if used_queries else None,
    }

def collect_bing_profiles(payload, username_variations, selected_platforms):
    if not has_public_search_fallback():
        return [], {"used": False, "queries": 0, "provider": None}

    search_url = current_app.config.get("BING_SEARCH_URL", "https://www.bing.com/search")
    timeout = float(current_app.config.get("SEARCH_REQUEST_TIMEOUT", 3.5)) + 2
    limit = int(current_app.config.get("BING_RESULTS_PER_QUERY", 8))

    max_queries = 1 if payload.precision_mode else 2
    queries: list[str] = []
    for variation in username_variations[:2]:
        queries.append(_build_serper_query(variation.username))
    queries = list(dict.fromkeys([q for q in queries if q]))[:max_queries]

    raw_results: list[dict] = []
    used_queries = 0
    import logging
    for q in queries:
        try:
            response = get_http_session().get(
                search_url,
                params={"format": "rss", "q": q},
                timeout=timeout,
                allow_redirects=True,
            )
            response.raise_for_status()
        except Exception as e:
            logging.warning(f"[Bing RSS] Provider call failed or timed out: {e}")
            continue

        parsed = parse_bing_rss_feed(response.text, limit)
        for item in parsed.get("organic") or []:
            link = normalize_result_url(item.get("link"))
            if not link:
                continue
            raw_results.append(
                {
                    "title": collapse_whitespace(item.get("title") or ""),
                    "link": link,
                    "snippet": collapse_whitespace(item.get("snippet") or ""),
                }
            )
        used_queries += 1

    profiles: list[dict] = []
    for platform in selected_platforms:
        for profile in scan_platform(payload, username_variations, platform, raw_results):
            profile.setdefault("source", "bing_rss")
            profiles.append(profile)

    return profiles, {
        "used": bool(used_queries),
        "queries": used_queries,
        "provider": "bing_rss" if used_queries else None,
    }

def discover_profiles(payload, username_variations, selected_platforms):
    """
    Discover public profiles via search providers (Serper preferred, Bing RSS fallback).

    Safety/Compliance:
    - Uses public search results only (no scraping of platform-internal endpoints).
    - Does not bypass authentication or privacy controls.
    """
    # Backwards-compatible behavior for tests/older frontend:
    # - If Serper is configured, prefer Serper.
    # - Otherwise use Bing RSS fallback if enabled.
    import logging
    profiles, meta = collect_serper_profiles(payload, username_variations, selected_platforms)
    if profiles:
        return profiles, meta
    logging.warning("[Discover] Serper failed or returned no profiles, falling back to Bing RSS.")
    profiles, meta = collect_bing_profiles(payload, username_variations, selected_platforms)
    if not profiles:
        logging.error("[Discover] All provider calls failed, returning empty profile list.")
    return profiles, meta

def scan_platform(payload, username_variations, platform, raw_results):
    if not raw_results:
        return []

    collected: list[dict] = []
    for item in raw_results:
        url = normalize_result_url(item.get("link"))
        if not url:
            continue
        resolved = resolve_platform_from_url(url)
        if not resolved or resolved.slug != platform.slug:
            continue
        if not is_profile_like_url(platform, url):
            continue

        extracted = extract_username_from_url(platform, url)
        best_variation = select_best_variation(
            username_variations,
            extracted,
            item.get("title"),
            item.get("snippet"),
            url,
        )
        if not best_variation:
            continue

        score = best_variation.score
        if extracted and extracted == best_variation.username:
            score = min(100, score + 5)
        if payload.precision_mode:
            score = min(100, score + 2)

        collected.append(
            {
                "platform": platform.name,
                "platform_slug": platform.slug,
                "category": platform.category,
                "username": best_variation.username,
                "profile_url": url,
                "url": url,
                "match_score": score,
                "verification": "public_search",
                "confidence": _confidence_from_score(score),
                "match_reason": f"Public search: {best_variation.reason}",
                "source": "public_search",
                "title": collapse_whitespace(item.get("title") or ""),
                "snippet": collapse_whitespace(item.get("snippet") or ""),
            }
        )

    return collected


def probe_profile(*_args, **_kwargs):
    return None


def rerank_profiles_with_openai(payload, username_variations, profiles):
    if not should_ai_rerank(payload, profiles):
        return profiles, False

    try:
        from openai import OpenAI
    except Exception:
        return profiles, False

    api_key = current_app.config.get("OPENAI_API_KEY")
    if not api_key:
        return profiles, False

    max_candidates = int(current_app.config.get("OPENAI_MAX_RERANK_CANDIDATES", 12))
    model = current_app.config.get("OPENAI_RERANK_MODEL", "gpt-5-mini")
    timeout = float(current_app.config.get("OPENAI_TIMEOUT", 12))

    candidates = profiles[:max_candidates]
    variants = [v.username for v in username_variations[:5]]

    client = OpenAI(api_key=api_key, timeout=timeout)
    try:
        import json

        prompt = {
            "query_username": payload.username,
            "variants": variants,
            "candidates": [
                {
                    "platform": c.get("platform_slug"),
                    "url": c.get("profile_url") or c.get("url"),
                    "title": c.get("title"),
                    "snippet": c.get("snippet"),
                }
                for c in candidates
            ],
            "instructions": (
                "Rank candidates by likelihood they represent the same public profile for the query username. "
                "Use only the given title/snippet/url. Return JSON: {\"order\": [\"url\", ...]}."
            ),
        }

        response = client.responses.create(
            model=model,
            input=[{"role": "user", "content": [{"type": "input_text", "text": json.dumps(prompt)}]}],
        )
        text = (response.output_text or "").strip()
        parsed = json.loads(text) if text.startswith("{") else None
        order = parsed.get("order") if isinstance(parsed, dict) else None
        if not isinstance(order, list) or not order:
            return profiles, False

        by_url = {str((c.get("profile_url") or c.get("url") or "")).strip(): c for c in candidates}
        reranked = []
        seen = set()
        for url in order:
            url = str(url).strip()
            if url in by_url and url not in seen:
                reranked.append(by_url[url])
                seen.add(url)
        for c in candidates:
            url = str((c.get("profile_url") or c.get("url") or "")).strip()
            if url and url not in seen:
                reranked.append(c)
                seen.add(url)
        reranked.extend(profiles[len(candidates) :])
        return reranked, True
    except Exception:
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
