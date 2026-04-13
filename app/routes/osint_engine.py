from __future__ import annotations

from flask import Blueprint, current_app, request

from app.services.availability_service import check_username_availability
from app.services.content_pattern_service import analyze_content_patterns
from app.services.identity_service import match_identity
from app.services.profile_analysis_service import analyze_profile
from app.services.response_utils import api_fail, api_ok
from app.services.reverse_image_service import analyze_reverse_image, persist_image_hashes
from app.services.social_graph_service import build_social_graph
from app.services.tracking_service import serialize_watchlist_entry, upsert_watchlist_entry


osint_bp = Blueprint("osint_engine", __name__)


def _ensure_engine_enabled():
    if not bool(current_app.config.get("OSINT_ENGINE_ENABLED", True)):
        return api_fail("OSINT engine is disabled.", status=503, meta={"endpoint": "osint_engine"})
    return None


@osint_bp.post("/api/identity/match")
def identity_match():
    disabled = _ensure_engine_enabled()
    if disabled:
        return disabled
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip()
    if not username:
        return api_fail("username is required", status=400, meta={"endpoint": "identity_match"})

    result = match_identity(payload)
    return api_ok(result, meta={"endpoint": "identity_match", "version": "1"})


@osint_bp.post("/api/reverse-image")
def reverse_image():
    disabled = _ensure_engine_enabled()
    if disabled:
        return disabled
    file_obj = request.files.get("image")
    if not file_obj:
        return api_fail("image file is required", status=400, meta={"endpoint": "reverse_image"})

    try:
        analysis = analyze_reverse_image(file_obj, max_size_bytes=int(current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)))
        source_platform = str(request.form.get("source_platform") or "unknown").strip().lower()
        source_profile = str(request.form.get("source_profile") or "unknown").strip()
        hashes = analysis.get("hashes", {})
        if hashes.get("phash") and hashes.get("dhash") and source_profile:
            persist_image_hashes(
                source_platform=source_platform,
                source_profile=source_profile,
                phash=hashes["phash"],
                dhash=hashes["dhash"],
            )
        return api_ok(
            {
                "possible_matches": analysis.get("possible_matches", []),
                "hashes": hashes,
            },
            meta={"endpoint": "reverse_image", "version": "1"},
        )
    except ValueError as error:
        return api_fail(str(error), status=400, meta={"endpoint": "reverse_image"})


@osint_bp.post("/api/analyze-profile")
def analyze_profile_endpoint():
    disabled = _ensure_engine_enabled()
    if disabled:
        return disabled
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return api_fail("invalid payload", status=400, meta={"endpoint": "analyze_profile"})

    result = analyze_profile(payload, openai_api_key=current_app.config.get("OPENAI_API_KEY"))
    return api_ok(result, meta={"endpoint": "analyze_profile", "version": "1"})


@osint_bp.post("/api/social-graph/build")
def social_graph_build():
    disabled = _ensure_engine_enabled()
    if disabled:
        return disabled
    payload = request.get_json(silent=True) or {}
    profiles = payload.get("profiles") or []
    if not isinstance(profiles, list):
        return api_fail("profiles must be an array", status=400, meta={"endpoint": "social_graph_build"})

    result = build_social_graph(profiles)
    return api_ok(result, meta={"endpoint": "social_graph_build", "version": "1"})


@osint_bp.post("/api/username/check")
def username_check():
    disabled = _ensure_engine_enabled()
    if disabled:
        return disabled
    payload = request.get_json(silent=True) or {}
    username = str(payload.get("username") or "").strip().lstrip("@")
    if not username:
        return api_fail("username is required", status=400, meta={"endpoint": "username_check"})

    platforms = payload.get("platforms") or None
    if platforms is not None and not isinstance(platforms, list):
        return api_fail("platforms must be an array", status=400, meta={"endpoint": "username_check"})

    rows = check_username_availability(username, platforms=platforms)
    return api_ok({"results": rows}, meta={"endpoint": "username_check", "version": "1"})


@osint_bp.post("/api/content-pattern/analyze")
def content_pattern_analyze():
    disabled = _ensure_engine_enabled()
    if disabled:
        return disabled
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return api_fail("invalid payload", status=400, meta={"endpoint": "content_pattern_analyze"})

    result = analyze_content_patterns(payload)
    return api_ok(result, meta={"endpoint": "content_pattern_analyze", "version": "1"})


@osint_bp.post("/api/watchlist/upsert")
def watchlist_upsert():
    disabled = _ensure_engine_enabled()
    if disabled:
        return disabled
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return api_fail("invalid payload", status=400, meta={"endpoint": "watchlist_upsert"})

    try:
        row = upsert_watchlist_entry(payload)
    except ValueError as error:
        return api_fail(str(error), status=400, meta={"endpoint": "watchlist_upsert"})

    return api_ok({"watchlist": serialize_watchlist_entry(row)}, meta={"endpoint": "watchlist_upsert", "version": "1"})
