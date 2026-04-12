from flask import Blueprint, jsonify, render_template, request, send_file, session
from app.services.response_utils import api_error

from ..models import User
from ..services.billing import billing_enabled, get_user_entitlements
from ..services.feature_gating import any_feature_required
from ..services.permissions import (
    FEATURE_FULL_ACCESS,
    FEATURE_PLATFORM_DATING_CHAT_ALL,
    FEATURE_PLATFORM_INSTAGRAM,
    FEATURE_PLATFORM_SOCIAL_ALL,
    FEATURE_PLATFORM_TIKTOK,
    has_permission,
)
from ..services.search_service import (
    PLATFORM_INDEX,
    SearchValidationError,
    build_search_payload,
    execute_search,
    list_platform_cards,
    resolve_uploaded_image,
)


search_bp = Blueprint("search", __name__)


@search_bp.route("/", methods=["GET"])
def home():
    return render_template("home.html", platforms=PLATFORM_INDEX.values())


@search_bp.route("/search", methods=["GET"])
@any_feature_required(
    FEATURE_PLATFORM_INSTAGRAM,
    FEATURE_PLATFORM_TIKTOK,
    FEATURE_PLATFORM_SOCIAL_ALL,
    FEATURE_PLATFORM_DATING_CHAT_ALL,
    FEATURE_FULL_ACCESS,
)
def search():
    return render_template(
        "search.html",
        platforms=PLATFORM_INDEX.values(),
        results=[],
        page=1,
        total_pages=None,
        query=request.args.get("query", "").strip(),
    )


@search_bp.route("/platforms", methods=["GET"])
@any_feature_required(
    FEATURE_PLATFORM_INSTAGRAM,
    FEATURE_PLATFORM_TIKTOK,
    FEATURE_PLATFORM_SOCIAL_ALL,
    FEATURE_PLATFORM_DATING_CHAT_ALL,
    FEATURE_FULL_ACCESS,
)
def platforms():
    return jsonify(list_platform_cards())


@search_bp.route("/api/search", methods=["POST"])
def api_search():
    from app.services.response_utils import check_rate_limit
    allowed, remaining = check_rate_limit("/api/search")
    if not allowed:
        import logging
        logging.warning("/api/search rate limit hit for IP %s", request.remote_addr)
        return api_error("Rate limit exceeded. Bitte warte kurz.", status=429)
    import logging
    import os, logging
    try:
        payload = build_search_payload(request.form)
        user_id = session.get("user_id")
        from app.extensions.main import db
        user = db.session.get(User, user_id) if user_id else None
        entitlements = get_user_entitlements(user)

        SEARCH_DEV_BYPASS = os.environ.get("SEARCH_DEV_BYPASS", "false").lower() == "true"
        if SEARCH_DEV_BYPASS:
            logging.warning("SEARCH_DEV_BYPASS_ACTIVE: path=/api/search username=%r platforms=%r", payload.username, payload.platforms)

        if billing_enabled() and not SEARCH_DEV_BYPASS:
            if not user:
                return api_error("Bitte melde dich an, um ShadowSeek zu nutzen.", status=401, errors={"feature_gating": True})
            if not entitlements.get("enabled_platforms"):
                return api_error("Dein aktuelles Abo erlaubt keine Username-Suche.", status=403, errors={"feature_gating": True, "entitlements": entitlements})
            for platform in payload.platforms:
                if platform not in entitlements.get("enabled_platforms", []):
                    return api_error(f"Dein aktuelles Abo erlaubt keine Suche auf: {platform}.", status=403, errors={"required": entitlements.get("enabled_platforms", []), "missing": platform, "feature_gating": True})
            # DeepSearch wird aktuell nur in Abo 4 via full_access erlaubt.
            if payload.deep_search and not has_permission(user, FEATURE_FULL_ACCESS):
                return api_error("DeepSearch ist in deinem aktuellen Abo nicht freigeschaltet.", status=403, errors={"feature_gating": True, "entitlements": entitlements})

        result = execute_search(
            payload,
            request.host_url,
            request.files.get("image"),
        )
        if billing_enabled() and not SEARCH_DEV_BYPASS:
            result["entitlements"] = entitlements
        # API contract: keep payload lean for the frontend renderer/tests.
        result.pop("query", None)
        result.pop("username_variations", None)
        # Legacy API contract for frontend/tests: return payload directly.
        return jsonify(result), 200
    except SearchValidationError as error:
        logging.warning(f"[Search] Validation error: {error.errors}")
        return api_error("Validation error", status=400, errors=error.errors)
    except Exception as exc:
        logging.exception(f"[Search] Unexpected error in /api/search: {exc}")
        return jsonify({"success": False, "error": "Internal server error"}), 500


@search_bp.route("/api/reverse-image/<token>", methods=["GET"])
def reverse_image_asset(token):
    from app.services.response_utils import api_error
    try:
        image_path, mime_type = resolve_uploaded_image(token)
        return send_file(image_path, mimetype=mime_type, conditional=True, max_age=300)
    except SearchValidationError as err:
        return api_error("Der Reverse-Image-Link ist ungueltig oder abgelaufen.", status=404, errors=getattr(err, "errors", None))
