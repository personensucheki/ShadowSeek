from __future__ import annotations

import re
from collections import OrderedDict

from flask import current_app

from .availability_service import check_username_availability
from .geo_service import normalize_location
from .score_utils import confidence_from_score, score_from_evidence
from .tiktok_service import TikTokService, extract_public_links_from_bio
from .youtube_service import YouTubeService


URL_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)


def match_identity(payload: dict) -> dict:
    normalized = _normalize_input(payload)
    variants = _generate_variants(normalized)

    youtube = YouTubeService(current_app.config.get("YOUTUBE_API_KEY"))
    tiktok = TikTokService()

    candidates = []

    yt_result = youtube.search_channels(normalized["username"], limit=8)
    for item in yt_result.get("items", []):
        candidates.append(_normalize_candidate(item, known_platform=normalized.get("known_platform"), source="youtube"))

    tt_candidates = tiktok.search_profile_candidates(variants)
    for item in tt_candidates:
        candidates.append(_normalize_candidate(item, known_platform=normalized.get("known_platform"), source="tiktok"))

    availability = check_username_availability(normalized["username"], platforms=["instagram", "tiktok", "youtube", "twitch", "reddit", "telegram"]) 
    for row in availability:
        if row["state"] in {"claimed", "likely_claimed"}:
            candidates.append(
                {
                    "platform": row["platform"],
                    "username": normalized["username"],
                    "display_name": normalized.get("realname") or normalized["username"],
                    "bio": "",
                    "links": [{"url": row["url"], "type": "public_link"}],
                    "avatar_url": None,
                    "evidence": [{"type": "availability", "value": row["state"], "weight": 10 if row["state"] == "claimed" else 6}],
                    "match_reasons": [f"username_{row['state']}"],
                }
            )

    deduped = _dedupe_candidates(candidates)
    profiles = []
    for candidate in deduped:
        evidence = candidate.get("evidence") or []
        score = score_from_evidence(evidence, base=35)
        confidence = confidence_from_score(score)
        candidate["score"] = score
        candidate["confidence"] = confidence
        candidate["match_reasons"] = sorted(set(candidate.get("match_reasons") or []))
        profiles.append(candidate)

    profiles.sort(key=lambda item: item.get("score", 0), reverse=True)

    geo = normalize_location(normalized.get("plz"), normalized.get("bio") or "")

    return {
        "profiles": profiles,
        "meta": {
            "variant_count": len(variants),
            "candidate_count": len(candidates),
            "deduped_count": len(profiles),
            "geo_signal": geo,
            "integrations": {
                "youtube_enabled": yt_result.get("enabled", False),
                "tiktok_enabled": True,
            },
        },
    }


def _normalize_input(payload: dict) -> dict:
    username = str(payload.get("username") or "").strip().lstrip("@").lower()
    return {
        "username": re.sub(r"[^a-z0-9._-]", "", username),
        "realname": str(payload.get("realname") or "").strip(),
        "clanname": str(payload.get("clanname") or "").strip(),
        "plz": str(payload.get("plz") or "").strip(),
        "bio": str(payload.get("bio") or "").strip(),
        "known_platform": str(payload.get("known_platform") or "").strip().lower(),
    }


def _generate_variants(normalized: dict) -> list[str]:
    base = normalized["username"]
    realname = normalized.get("realname") or ""
    clanname = normalized.get("clanname") or ""

    variants = OrderedDict()
    for value in [base, base.replace(".", ""), f"{base}_official", f"real{base}"]:
        if value:
            variants[value] = True

    tokens = [re.sub(r"[^a-z0-9]", "", token.lower()) for token in realname.split() if token.strip()]
    if tokens:
        variants["".join(tokens)] = True
        variants[".".join(tokens)] = True
    if clanname:
        compact = re.sub(r"[^a-z0-9]", "", clanname.lower())
        variants[f"{base}{compact}"] = True

    return list(variants.keys())[:10]


def _normalize_candidate(candidate: dict, *, known_platform: str, source: str) -> dict:
    platform = str(candidate.get("platform") or source).lower()
    username = str(candidate.get("username") or "").strip().lstrip("@")
    bio = str(candidate.get("bio") or "")
    links = candidate.get("links") or extract_public_links_from_bio(bio)

    evidence = []
    if username:
        evidence.append({"type": "username_match", "value": username, "weight": 30})
    if links:
        evidence.append({"type": "public_links", "value": len(links), "weight": 10})
    if known_platform and platform == known_platform:
        evidence.append({"type": "known_platform", "value": known_platform, "weight": 15})

    match_reasons = ["public_signal_match"]
    if known_platform and platform == known_platform:
        match_reasons.append("known_platform_match")

    return {
        "platform": platform,
        "username": username,
        "display_name": candidate.get("display_name") or username,
        "bio": bio,
        "links": links,
        "avatar_url": candidate.get("avatar_url"),
        "evidence": evidence,
        "match_reasons": match_reasons,
    }


def _dedupe_candidates(candidates: list[dict]) -> list[dict]:
    deduped = {}
    for item in candidates:
        key = (item.get("platform"), item.get("username"))
        if key not in deduped:
            deduped[key] = item
            continue
        existing = deduped[key]
        if len(item.get("evidence") or []) > len(existing.get("evidence") or []):
            deduped[key] = item
    return list(deduped.values())
