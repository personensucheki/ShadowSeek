from __future__ import annotations

from collections import Counter
from datetime import datetime

from .search_service import (
    PLATFORM_INDEX,
    SearchPayload,
    SearchValidationError,
    execute_search,
    normalize_ascii,
    normalize_handle,
)


PULSE_DEFAULT_PLATFORMS = ("tiktok", "twitch", "youtube")


def run_creator_profile_scan(
    creator_query: str,
    request_base_url: str,
    platform_slug: str | None = None,
    deep_search: bool = True,
):
    raw_query = normalize_ascii(creator_query)
    username = normalize_handle(raw_query)
    if not username or len(username) < 2:
        raise SearchValidationError(
            {"nutzername": "Bitte mindestens einen gueltigen Creator-Namen eingeben."}
        )

    payload = SearchPayload(
        username=username,
        real_name=raw_query if " " in raw_query else "",
        clan_name="",
        age="",
        postal_code="",
        deep_search=deep_search,
        platforms=resolve_platform_scope(platform_slug),
    )

    result = execute_search(payload, request_base_url)
    profiles = [enrich_profile(profile) for profile in result.get("profiles", [])]
    result["profiles"] = profiles
    result["query"]["creator_text"] = raw_query
    result["summary"] = build_scan_summary(profiles)
    return result


def build_query_rows(scan_result):
    generated_at = format_generated_at(scan_result.get("meta", {}).get("generated_at"))
    return [
        {
            "zeitpunkt": generated_at,
            "platform": profile["platform"],
            "quelle": profile["username"],
            "typ": profile["verification"],
            "score": profile["match_score"],
            "confidence": profile["confidence"],
            "details": profile["match_reason"],
            "profile_url": profile["profile_url"],
            "source": profile.get("source", "direct"),
            "title": profile.get("title", ""),
            "snippet": profile.get("snippet", ""),
        }
        for profile in scan_result.get("profiles", [])
    ]


def build_live_rows(scan_result):
    generated_at = format_generated_at(scan_result.get("meta", {}).get("generated_at"))
    return [
        {
            "zeitpunkt": generated_at,
            "quelle": profile["username"],
            "typ": profile["verification"],
            "score": profile["match_score"],
            "confidence": profile["confidence"],
            "details": profile["match_reason"],
            "profile_url": profile["profile_url"],
            "platform": profile["platform"],
            "platform_slug": profile["platform_slug"],
            "source": profile.get("source", "direct"),
        }
        for profile in scan_result.get("profiles", [])
    ]


def resolve_platform_scope(platform_slug: str | None):
    slug = normalize_handle(platform_slug or "")
    if slug in PLATFORM_INDEX:
        return (slug,)
    return tuple(PULSE_DEFAULT_PLATFORMS)


def build_scan_summary(profiles):
    verified_hits = sum(
        1
        for profile in profiles
        if profile.get("verification") in {"confirmed", "ai_reranked", "search"}
    )
    platform_counts = Counter(profile["platform"] for profile in profiles)
    average_score = (
        round(
            sum(profile.get("match_score", 0) for profile in profiles) / len(profiles),
            1,
        )
        if profiles
        else 0.0
    )

    return {
        "total_hits": len(profiles),
        "verified_hits": verified_hits,
        "average_score": average_score,
        "platforms": [
            {"platform": platform, "count": count}
            for platform, count in platform_counts.most_common()
        ],
        "top_hit": profiles[0] if profiles else None,
    }


def enrich_profile(profile):
    enriched = dict(profile)
    enriched["confidence"] = derive_confidence(profile)
    return enriched


def derive_confidence(profile):
    score = int(profile.get("match_score") or 0)
    verification = str(profile.get("verification") or "").lower()

    if verification in {"confirmed", "ai_reranked"} and score >= 88:
        return "high"
    if verification in {"confirmed", "search", "ai_reranked"} or score >= 74:
        return "medium"
    return "low"


def format_generated_at(value):
    if not value:
        return "-"

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value

    return parsed.strftime("%d.%m.%Y %H:%M")
