from __future__ import annotations

import json
import mimetypes
import re
import threading
import unicodedata
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse

import requests
from flask import current_app, url_for
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from openai import OpenAI
from pydantic import BaseModel, Field
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
SERPER_SOURCE = "serper"
DIRECT_SOURCE = "direct"
_thread_local = threading.local()
_openai_lock = threading.Lock()
_openai_client = None


@dataclass(frozen=True)
class PlatformDefinition:
    slug: str
    name: str
    category: str
    profile_url: str
    domains: tuple[str, ...]
    excluded_segments: tuple[str, ...] = ()
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


class RerankCandidate(BaseModel):
    candidate_id: str
    score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=240)


class RerankResponse(BaseModel):
    ranked: list[RerankCandidate]


PLATFORMS = (
    PlatformDefinition(
        slug="instagram",
        name="Instagram",
        category="social",
        profile_url="https://www.instagram.com/{username}/",
        domains=("instagram.com",),
        excluded_segments=("p", "reel", "reels", "stories", "explore", "accounts"),
        not_found_markers=("page isn't available", "sorry, this page isn't available"),
    ),
    PlatformDefinition(
        slug="tiktok",
        name="TikTok",
        category="social",
        profile_url="https://www.tiktok.com/@{username}",
        domains=("tiktok.com",),
        excluded_segments=("discover", "tag", "search", "music"),
        not_found_markers=("couldn't find this account",),
    ),
    PlatformDefinition(
        slug="x",
        name="Twitter/X",
        category="social",
        profile_url="https://x.com/{username}",
        domains=("x.com", "twitter.com"),
        excluded_segments=("home", "explore", "search", "i", "hashtag", "messages", "compose"),
        not_found_markers=("this account doesn't exist",),
    ),
    PlatformDefinition(
        slug="youtube",
        name="YouTube",
        category="video",
        profile_url="https://www.youtube.com/@{username}",
        domains=("youtube.com",),
        excluded_segments=("watch", "results", "playlist", "shorts", "feed"),
        not_found_markers=("this page isn't available",),
    ),
    PlatformDefinition(
        slug="twitch",
        name="Twitch",
        category="streaming",
        profile_url="https://www.twitch.tv/{username}",
        domains=("twitch.tv",),
        excluded_segments=("directory", "downloads", "jobs", "store", "settings"),
        not_found_markers=("sorry. unless you've got a time machine",),
    ),
    PlatformDefinition(
        slug="reddit",
        name="Reddit",
        category="community",
        profile_url="https://www.reddit.com/user/{username}/",
        domains=("reddit.com",),
        excluded_segments=("r", "search", "media", "topics"),
        not_found_markers=("nobody on reddit goes by that name",),
    ),
    PlatformDefinition(
        slug="telegram",
        name="Telegram",
        category="messaging",
        profile_url="https://t.me/{username}",
        domains=("t.me", "telegram.me"),
        excluded_segments=("share", "addstickers", "s", "blog"),
    ),
    PlatformDefinition(
        slug="onlyfans",
        name="OnlyFans",
        category="subscription",
        profile_url="https://onlyfans.com/{username}",
        domains=("onlyfans.com",),
        excluded_segments=("login", "signup", "my", "posts"),
        not_found_markers=("page not found", "error code 404"),
    ),
    PlatformDefinition(
        slug="github",
        name="GitHub",
        category="developer",
        profile_url="https://github.com/{username}",
        domains=("github.com",),
        excluded_segments=("topics", "explore", "features", "marketplace", "orgs", "settings"),
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
    reverse_image_links = {}
    serper_meta = {"used": False, "queries": 0}
    ai_reranking_applied = False
    profiles = []

    if has_serper_api_key():
        serper_profiles, serper_meta = collect_serper_profiles(payload, username_variations)
        profiles.extend(serper_profiles)

    covered_slugs = {profile["platform_slug"] for profile in profiles}
    missing_slugs = [slug for slug in payload.platforms if slug not in covered_slugs]
    if missing_slugs:
        profiles.extend(discover_profiles(payload, username_variations, missing_slugs))

    profiles = dedupe_and_limit_profiles(profiles, payload.deep_search)

    if should_ai_rerank(payload, profiles):
        profiles, ai_reranking_applied = rerank_profiles_with_openai(
            payload,
            username_variations,
            profiles,
        )

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
            "ai_reranking_applied": ai_reranking_applied,
            "serper_used": serper_meta["used"],
            "serper_queries": serper_meta["queries"],
        },
    }


def collect_serper_profiles(payload, username_variations):
    queries = build_serper_queries(payload, username_variations)
    if not queries:
        return [], {"used": False, "queries": 0}

    max_workers = min(len(queries), max(1, min(current_app.config["SEARCH_MAX_WORKERS"], 4)))
    serper_config = {
        "api_url": current_app.config["SERPER_API_URL"],
        "api_key": current_app.config["SERPER_API_KEY"],
        "gl": current_app.config["SERPER_GL"],
        "hl": current_app.config["SERPER_HL"],
        "num": current_app.config["SERPER_RESULTS_PER_QUERY"],
        "timeout": current_app.config["SEARCH_REQUEST_TIMEOUT"] + 2,
    }
    parsed_profiles = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(run_serper_query, query, serper_config): query
            for query in queries
        }
        for future in as_completed(future_map):
            query = future_map[future]
            try:
                response_data = future.result()
            except requests.RequestException:
                continue
            parsed_profiles.extend(
                parse_serper_profiles(payload, username_variations, response_data, query)
            )

    return dedupe_and_limit_profiles(parsed_profiles, payload.deep_search), {
        "used": bool(parsed_profiles),
        "queries": len(queries),
    }


def build_serper_queries(payload, username_variations):
    query_limit = 8 if payload.deep_search else 4
    variation_terms = [variation.username for variation in username_variations[:query_limit]]
    site_clause = build_site_clause(payload.platforms)
    queries = []

    for chunk in chunked(variation_terms, 3 if payload.deep_search else 4):
        quoted_variations = " OR ".join(f'"{term}"' for term in chunk)
        queries.append(f"({quoted_variations}) {site_clause}")

    if payload.deep_search:
        context_terms = []
        if payload.real_name:
            context_terms.append(f'"{payload.real_name}"')
        if payload.clan_name:
            context_terms.append(f'"{payload.clan_name}"')
        if payload.postal_code:
            context_terms.append(f'"{payload.postal_code}"')
        if context_terms:
            queries.append(f'"{payload.username}" {" ".join(context_terms[:2])} {site_clause}')

    return list(dict.fromkeys(queries))[:4]


def build_site_clause(platform_slugs):
    domains = []
    for slug in platform_slugs:
        domains.extend(PLATFORM_INDEX[slug].domains)
    unique_domains = sorted(dict.fromkeys(domains))
    return "(" + " OR ".join(f"site:{domain}" for domain in unique_domains) + ")"


def run_serper_query(query, serper_config):
    response = get_http_session().post(
        serper_config["api_url"],
        headers={
            "X-API-KEY": serper_config["api_key"],
            "Content-Type": "application/json",
        },
        json={
            "q": query,
            "gl": serper_config["gl"],
            "hl": serper_config["hl"],
            "num": serper_config["num"],
        },
        timeout=serper_config["timeout"],
    )
    response.raise_for_status()
    return response.json()


def parse_serper_profiles(payload, username_variations, response_data, query):
    organic_results = response_data.get("organic") or []
    candidates = []

    for result in organic_results:
        profile = build_serper_candidate(payload, username_variations, result, query)
        if profile:
            candidates.append(profile)

    return verify_serper_candidates(candidates)


def build_serper_candidate(payload, username_variations, result, query):
    link = normalize_result_url(result.get("link"))
    if not link:
        return None

    platform = resolve_platform_from_url(link)
    if not platform or platform.slug not in payload.platforms:
        return None

    extracted_username = extract_username_from_url(platform, link)
    if not extracted_username:
        return None

    title = result.get("title") or ""
    snippet = result.get("snippet") or ""
    matched_variation = select_best_variation(
        username_variations,
        extracted_username,
        title,
        snippet,
        link,
    )
    if not matched_variation:
        return None

    position = int(result.get("position") or 10)
    score = compute_serper_score(matched_variation, extracted_username, title, snippet, position)

    return {
        "platform": platform.name,
        "platform_slug": platform.slug,
        "category": platform.category,
        "username": extracted_username,
        "profile_url": link,
        "match_score": score,
        "verification": "search",
        "match_reason": f"{matched_variation.reason} via Google/Serper",
        "http_status": "SERP",
        "source": SERPER_SOURCE,
        "query": query,
        "title": title,
        "snippet": snippet,
    }


def compute_serper_score(variation, extracted_username, title, snippet, position):
    score = variation.score - min((position - 1) * 2, 12)
    extracted_normalized = normalize_handle(extracted_username)
    title_text = normalize_ascii(title).lower()
    snippet_text = normalize_ascii(snippet).lower()

    if extracted_normalized == variation.username:
        score += 8
    if variation.username in title_text:
        score += 4
    if variation.username in snippet_text:
        score += 3

    return max(55, min(score, 99))


def verify_serper_candidates(candidates):
    if not candidates:
        return []

    grouped = {}
    for candidate in sorted(candidates, key=lambda item: item["match_score"], reverse=True):
        grouped.setdefault(candidate["platform_slug"], []).append(candidate)

    verified = []
    timeout = current_app.config["SEARCH_REQUEST_TIMEOUT"]

    for platform_slug, items in grouped.items():
        platform = PLATFORM_INDEX[platform_slug]
        for candidate in items[:2]:
            profile = verify_candidate_url(platform, candidate, timeout)
            verified.append(profile or candidate)

    return verified


def verify_candidate_url(platform, candidate, timeout):
    response = None

    try:
        response = get_http_session().get(
            candidate["profile_url"],
            timeout=timeout,
            allow_redirects=True,
            stream=True,
        )
        status_code = response.status_code
        if status_code in {401, 403, 404, 410, 429} or status_code >= 500:
            return None

        preview = read_response_preview(response)
        final_url = normalize_result_url(response.url)
        if not final_url:
            return None

        final_username = extract_username_from_url(platform, final_url)
        if not final_username:
            return None

        if any(marker in preview or marker in final_url.lower() for marker in platform.not_found_markers):
            return None

        profile = dict(candidate)
        profile["profile_url"] = final_url
        profile["username"] = final_username
        profile["verification"] = "confirmed"
        profile["http_status"] = status_code
        return profile
    except requests.RequestException:
        return None
    finally:
        if response is not None:
            response.close()


def discover_profiles(payload, username_variations, platform_slugs=None):
    selected_slugs = list(platform_slugs or payload.platforms)
    if not selected_slugs:
        return []

    platforms = [PLATFORM_INDEX[slug] for slug in selected_slugs]
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

    return dedupe_and_limit_profiles(hits, payload.deep_search)


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
        final_url = normalize_result_url(response.url)
        lower_username = variation.username.lower()

        if any(marker in final_url.lower() or marker in preview for marker in platform.not_found_markers):
            return None

        verification = "confirmed"
        score = variation.score

        if lower_username not in final_url.lower() and lower_username not in preview:
            score -= 7
            verification = "likely"

        if any(token in final_url.lower() for token in ("/login", "/signup", "/auth")):
            score -= 5
            verification = "likely"

        return {
            "platform": platform.name,
            "platform_slug": platform.slug,
            "category": platform.category,
            "username": variation.username,
            "profile_url": final_url,
            "match_score": max(score, 50),
            "verification": verification,
            "match_reason": variation.reason,
            "http_status": status_code,
            "source": DIRECT_SOURCE,
            "title": "",
            "snippet": "",
        }
    except requests.RequestException:
        return None
    finally:
        if response is not None:
            response.close()


def rerank_profiles_with_openai(payload, username_variations, profiles):
    candidates = profiles[: current_app.config["OPENAI_MAX_RERANK_CANDIDATES"]]
    indexed_candidates = []
    for index, profile in enumerate(candidates, start=1):
        indexed_candidates.append(
            {
                "candidate_id": f"c{index}",
                "platform": profile["platform"],
                "username": profile["username"],
                "url": profile["profile_url"],
                "score": profile["match_score"],
                "verification": profile["verification"],
                "reason": profile["match_reason"],
                "title": profile.get("title", ""),
                "snippet": profile.get("snippet", ""),
                "source": profile.get("source", DIRECT_SOURCE),
            }
        )

    prompt = {
        "target": {
            "username": payload.username,
            "real_name": payload.real_name,
            "clan_name": payload.clan_name,
            "age": payload.age,
            "postal_code": payload.postal_code,
            "deep_search": payload.deep_search,
            "variations": [variation.username for variation in username_variations],
        },
        "candidates": indexed_candidates,
    }

    try:
        response = get_openai_client().responses.parse(
            model=current_app.config["OPENAI_RERANK_MODEL"],
            input=json.dumps(prompt, ensure_ascii=True),
            instructions=(
                "You rerank likely social profile matches for one person. "
                "Prefer exact username matches, plausible handle variations, and URLs that are clearly user profiles. "
                "Penalize login pages, post URLs, hashtags, communities, and generic landing pages. "
                "Return only the strongest candidates."
            ),
            text_format=RerankResponse,
            max_output_tokens=500,
            temperature=0,
            timeout=current_app.config["OPENAI_TIMEOUT"],
            verbosity="low",
        )
        parsed = getattr(response, "output_parsed", None)
        if not parsed or not parsed.ranked:
            return profiles, False
    except Exception:
        return profiles, False

    indexed_map = {item["candidate_id"]: item for item in indexed_candidates}
    profile_map = {profile["profile_url"]: profile for profile in candidates}
    reranked = []

    for item in parsed.ranked:
        source_candidate = indexed_map.get(item.candidate_id)
        if not source_candidate:
            continue
        original = profile_map.get(source_candidate["url"])
        if not original:
            continue

        enriched = dict(original)
        enriched["match_score"] = max(original["match_score"], item.score)
        enriched["match_reason"] = item.reason
        enriched["verification"] = "ai_reranked"
        reranked.append(enriched)

    if not reranked:
        return profiles, False

    ranked_urls = {profile["profile_url"] for profile in reranked}
    remainder = [profile for profile in profiles if profile["profile_url"] not in ranked_urls]
    return dedupe_and_limit_profiles(reranked + remainder, payload.deep_search), True


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
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
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


def get_openai_client():
    global _openai_client

    if _openai_client is None:
        with _openai_lock:
            if _openai_client is None:
                _openai_client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
    return _openai_client


def has_serper_api_key():
    return bool(current_app.config.get("SERPER_API_KEY"))


def should_ai_rerank(payload, profiles):
    return bool(
        payload.deep_search
        and current_app.config.get("OPENAI_API_KEY")
        and len(profiles) > 1
    )


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


def normalize_result_url(url):
    if not url:
        return None

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return None

    clean_path = parsed.path.rstrip("/") or "/"
    return parsed._replace(query="", fragment="", path=clean_path).geturl()


def resolve_platform_from_url(url):
    parsed = urlparse(url)
    hostname = (parsed.netloc or "").lower().replace("www.", "")

    for platform in PLATFORMS:
        if any(hostname == domain or hostname.endswith(f".{domain}") for domain in platform.domains):
            return platform
    return None


def extract_username_from_url(platform, url):
    parsed = urlparse(url)
    segments = [segment for segment in parsed.path.split("/") if segment]
    if not segments:
        return None

    if platform.slug == "tiktok":
        if segments[0].startswith("@"):
            return normalize_handle(segments[0][1:])
        return None

    if platform.slug == "youtube":
        if segments[0].startswith("@"):
            return normalize_handle(segments[0][1:])
        return None

    if platform.slug == "reddit":
        if len(segments) >= 2 and segments[0] in {"user", "u"}:
            return normalize_handle(segments[1])
        return None

    first_segment = segments[0]
    if first_segment.startswith("@"):
        first_segment = first_segment[1:]

    if first_segment.lower() in platform.excluded_segments:
        return None

    return normalize_handle(first_segment)


def select_best_variation(username_variations, extracted_username, title, snippet, url):
    haystack = " ".join(
        (
            normalize_ascii(extracted_username).lower(),
            normalize_ascii(title).lower(),
            normalize_ascii(snippet).lower(),
            normalize_ascii(url).lower(),
        )
    )
    best = None
    best_score = -1

    for variation in username_variations:
        score = 0
        if variation.username == normalize_handle(extracted_username):
            score += variation.score + 12
        elif variation.username in haystack:
            score += variation.score + 4
        else:
            continue

        if score > best_score:
            best = variation
            best_score = score

    return best


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


def chunked(items, chunk_size):
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]
