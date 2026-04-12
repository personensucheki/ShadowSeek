from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Iterable

import requests
from flask import Blueprint, jsonify, request

from ..services.search_service import PLATFORM_INDEX


suggest_bp = Blueprint("suggest", __name__, url_prefix="/api/suggest")


@dataclass(frozen=True)
class _CacheEntry:
    expires_at: float
    suggestions: list[str]


_CACHE: dict[tuple[str, str], _CacheEntry] = {}
_CACHE_TTL_SECONDS = 10 * 60
_MAX_QUERY_LEN = 80
_MAX_SUGGESTIONS = 10


def _now() -> float:
    return time.time()


def _normalize_query(value: str) -> str:
    value = (value or "").strip()
    value = " ".join(value.split())
    return value[:_MAX_QUERY_LEN]


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        item = (item or "").strip()
        if not item:
            continue
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
        if len(out) >= _MAX_SUGGESTIONS:
            break
    return out


def _shadowseek_suggestions(q: str) -> list[str]:
    q_lower = q.casefold()
    platforms = [p.name for p in PLATFORM_INDEX.values()]
    platform_hits = [p for p in platforms if q_lower in p.casefold()]

    templates = [
        "{q}",
        "{q} login",
        "{q} profil",
        "{q} konto",
        "{q} kontakt",
        "{q} support",
    ]
    # leichte OSINT-typische Ergänzungen, ohne "grauzonen" / Umgehung
    osint_templates = [
        "{q} username",
        "{q} account",
        "{q} site:{platform}",
    ]

    suggestions: list[str] = []
    suggestions.extend(platform_hits[:4])
    suggestions.extend([t.format(q=q) for t in templates])
    for platform in platform_hits[:3]:
        suggestions.append(osint_templates[-1].format(q=q, platform=f"{platform.lower()}.com"))
    suggestions.extend([t.format(q=q) for t in osint_templates[:-1]])
    return _dedupe(suggestions)


def _duckduckgo_suggestions(q: str) -> list[str]:
    # DuckDuckGo AutoComplete (public). Fallback bleibt lokal, wenn dies fehlschlägt.
    response = requests.get(
        "https://duckduckgo.com/ac/",
        params={"q": q, "type": "list"},
        timeout=2.5,
        headers={"User-Agent": "ShadowSeek/1.0"},
    )
    response.raise_for_status()
    data = response.json()
    phrases: list[str] = []
    if isinstance(data, list):
        # Format A: ["facebook", ["facebook", "facebook login", ...]]
        if len(data) >= 2 and isinstance(data[1], list):
            phrases.extend([item for item in data[1] if isinstance(item, str)])
        # Format B: [{"phrase": "..."} ...] (älteres Format)
        for item in data:
            if isinstance(item, dict):
                phrase = item.get("phrase")
                if isinstance(phrase, str):
                    phrases.append(phrase)
    return _dedupe(phrases)


@suggest_bp.route("", methods=["GET"])
def suggest():
    from app.services.response_utils import check_rate_limit
    allowed, remaining = check_rate_limit("/api/suggest")
    if not allowed:
        import logging
        logging.warning("/api/suggest rate limit hit for IP %s", request.remote_addr)
        return api_error("Rate limit exceeded. Bitte warte kurz.", status=429)
    q = _normalize_query(request.args.get("q", ""))
    engine = (request.args.get("engine", "shadowseek") or "shadowseek").strip().lower()

    from app.services.response_utils import api_success, api_error
    import logging
    if len(q) < 1:
        return api_success({"query": q, "engine": engine, "suggestions": []})

    cache_key = (engine, q.casefold())
    cached = _CACHE.get(cache_key)
    if cached and cached.expires_at > _now():
        return api_success({"query": q, "engine": engine, "suggestions": cached.suggestions})

    suggestions: list[str]
    if engine == "shadowseek":
        suggestions = _shadowseek_suggestions(q)
    else:
        try:
            suggestions = _duckduckgo_suggestions(q)
        except Exception as e:
            logging.warning(f"[Suggest] DuckDuckGo provider failed or timed out: {e}")
            suggestions = _shadowseek_suggestions(q)

    _CACHE[cache_key] = _CacheEntry(expires_at=_now() + _CACHE_TTL_SECONDS, suggestions=suggestions)
    return api_success({"query": q, "engine": engine, "suggestions": suggestions})
