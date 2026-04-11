from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..plugins.registry import run_plugins
from .image_similarity import compare_uploaded_against_gallery
from .risk_score import calculate_osint_risk
from .screenshot_engine import capture_profile_screenshot
from .username_similarity import find_similar_usernames


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_plugin_context(query: dict[str, Any]) -> dict[str, Any]:
    return {
        "username": query.get("base_username") or query.get("username") or None,
        "real_name": query.get("real_name") or None,
        "clan_name": query.get("clan_name") or None,
        "age": _safe_int(query.get("age")),
        "postal_code": query.get("postal_code") or None,
        "image_path": query.get("reference_image") or None,
        "deepsearch_enabled": bool(query.get("deepsearch_enabled", True)),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_deepsearch(
    query: dict[str, Any] | None,
    profiles: list[dict[str, Any]] | None = None,
    images: list[dict[str, Any]] | None = None,
    riskdata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Kombiniert mehrere Analyse-Module in eine stabile Response.
    Teilfehler bleiben lokal und brechen nicht die Gesamtantwort.
    """
    query = _safe_dict(query)
    result = {
        "similarity": {"matches": []},
        "screenshots": [],
        "image_similarity": {"matches": []},
        "risk_score": {"score": 0, "level": "low", "factors": []},
        "usernames": _safe_list(query.get("usernames")),
        "profiles": _safe_list(profiles if profiles is not None else query.get("profiles")),
        "images": _safe_list(images if images is not None else query.get("images")),
        "reverse_image": _safe_dict(query.get("reverse_image")),
        "plugin_results": {},
    }

    if query.get("base_username") and isinstance(query.get("candidates"), list):
        try:
            result["similarity"] = {
                "matches": find_similar_usernames(
                    query["base_username"],
                    query["candidates"],
                )
            }
        except Exception:
            result["similarity"] = {"matches": []}

    screenshots: list[dict[str, str]] = []
    for url in _safe_list(query.get("profile_urls")):
        try:
            shot = capture_profile_screenshot(url)
        except Exception:
            continue
        if shot.get("success") and shot.get("screenshot_path"):
            screenshots.append({"url": url, "path": shot["screenshot_path"]})
    result["screenshots"] = screenshots

    if query.get("reference_image") and isinstance(query.get("gallery"), list):
        try:
            image_similarity = compare_uploaded_against_gallery(
                query["reference_image"],
                query["gallery"],
            )
            if isinstance(image_similarity, dict) and isinstance(image_similarity.get("matches"), list):
                result["image_similarity"] = image_similarity
        except Exception:
            result["image_similarity"] = {"matches": []}

    risk_payload = riskdata if isinstance(riskdata, dict) else query.get("riskdata")
    if isinstance(risk_payload, dict):
        try:
            calculated_risk = calculate_osint_risk(risk_payload)
            if isinstance(calculated_risk, dict):
                result["risk_score"] = {
                    "score": int(calculated_risk.get("score", 0)),
                    "level": calculated_risk.get("level", "low"),
                    "factors": _safe_list(calculated_risk.get("factors")),
                }
        except Exception:
            result["risk_score"] = {"score": 0, "level": "low", "factors": []}

    result["plugin_results"] = run_plugins(_normalize_plugin_context(query))
    return result
