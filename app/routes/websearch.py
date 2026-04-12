from __future__ import annotations

import time
from dataclasses import dataclass

from flask import Blueprint, current_app, jsonify, request

from ..services.search_service import get_http_session, parse_bing_rss_feed, run_serper_query


websearch_bp = Blueprint("websearch", __name__, url_prefix="/api/websearch")


@dataclass(frozen=True)
class _CacheEntry:
    expires_at: float
    payload: dict


_CACHE: dict[tuple[str, str], _CacheEntry] = {}
_CACHE_TTL_SECONDS = 5 * 60
_MAX_QUERY_LEN = 120


def _now() -> float:
    return time.time()


def _normalize_query(raw: str) -> str:
    raw = (raw or "").strip()
    raw = " ".join(raw.split())
    return raw[:_MAX_QUERY_LEN]


def _serper_search(q: str) -> dict:
    api_key = current_app.config.get("SERPER_API_KEY")
    api_url = current_app.config.get("SERPER_API_URL")
    if not api_key or not api_url:
        raise RuntimeError("SERPER not configured")

    response_data = run_serper_query(
        q,
        {
            "api_url": api_url,
            "api_key": api_key,
            "gl": current_app.config.get("SERPER_GL", "de"),
            "hl": current_app.config.get("SERPER_HL", "de"),
            "num": int(current_app.config.get("SERPER_RESULTS_PER_QUERY", 8)),
            "timeout": float(current_app.config.get("SEARCH_REQUEST_TIMEOUT", 3.5)) + 2,
        },
    )

    organic = response_data.get("organic") or []
    results = []
    for item in organic:
        link = (item.get("link") or "").strip()
        title = (item.get("title") or "").strip()
        snippet = (item.get("snippet") or "").strip()
        if not link or not title:
            continue
        results.append({"title": title, "url": link, "snippet": snippet})

    return {"provider": "serper", "results": results}


def _bing_rss_search(q: str) -> dict:
    search_url = current_app.config.get("BING_SEARCH_URL", "https://www.bing.com/search")
    limit = int(current_app.config.get("BING_RESULTS_PER_QUERY", 8))
    timeout = float(current_app.config.get("SEARCH_REQUEST_TIMEOUT", 3.5)) + 2
    response = get_http_session().get(
        search_url,
        params={"format": "rss", "q": q},
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()
    parsed = parse_bing_rss_feed(response.text, limit)
    organic = parsed.get("organic") or []
    results = []
    for item in organic:
        link = (item.get("link") or "").strip()
        title = (item.get("title") or "").strip()
        snippet = (item.get("snippet") or "").strip()
        if not link or not title:
            continue
        results.append({"title": title, "url": link, "snippet": snippet})
    return {"provider": "bing_rss", "results": results}


@websearch_bp.route("", methods=["GET"])
def websearch():
    q = _normalize_query(request.args.get("q", ""))
    engine = (request.args.get("engine", "shadowseek") or "shadowseek").strip().lower()

    if not q:
        return jsonify({"query": q, "engine": engine, "provider": None, "results": []})

    cache_key = (engine, q.casefold())
    cached = _CACHE.get(cache_key)
    if cached and cached.expires_at > _now():
        return jsonify(cached.payload)

    provider_payload = None
    # "google" und "shadowseek" bevorzugen Serper (falls verfügbar).
    if engine in {"shadowseek", "google"}:
        try:
            provider_payload = _serper_search(q)
        except Exception:
            provider_payload = None

    if provider_payload is None:
        try:
            provider_payload = _bing_rss_search(q)
        except Exception:
            provider_payload = {"provider": None, "results": []}

    payload = {
        "query": q,
        "engine": engine,
        "provider": provider_payload.get("provider"),
        "results": provider_payload.get("results", []),
    }
    _CACHE[cache_key] = _CacheEntry(expires_at=_now() + _CACHE_TTL_SECONDS, payload=payload)
    return jsonify(payload)

