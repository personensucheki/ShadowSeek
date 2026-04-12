from flask import Blueprint, jsonify, render_template, request, send_file, session

from ..models import User
from ..services.billing import billing_enabled, get_user_entitlements
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
def platforms():
    return jsonify(list_platform_cards())


@search_bp.route("/api/search", methods=["POST"])
def api_search():
    try:
        payload = build_search_payload(request.form)
        user_id = session.get("user_id")
        user = User.query.get(user_id) if user_id else None
        entitlements = get_user_entitlements(user)

        if billing_enabled():
            if not user:
                return (
                    jsonify(
                        {
                            "error": "Bitte melde dich an, um ShadowSeek zu nutzen.",
                            "feature_gating": True,
                        }
                    ),
                    401,
                )
            if not entitlements["search_allowed"]:
                return (
                    jsonify(
                        {
                            "error": "Dein aktuelles Abo erlaubt keine Username-Suche.",
                            "feature_gating": True,
                            "entitlements": entitlements,
                        }
                    ),
                    403,
                )
            for platform in payload.platforms:
                if platform not in entitlements["enabled_platforms"]:
                    return (
                        jsonify(
                            {
                                "error": f"Dein aktuelles Abo erlaubt keine Suche auf: {platform}.",
                                "required": entitlements["enabled_platforms"],
                                "missing": platform,
                                "feature_gating": True,
                            }
                        ),
                        403,
                    )
            if payload.deep_search and not entitlements["deepsearch_allowed"]:
                return (
                    jsonify(
                        {
                            "error": "DeepSearch ist in deinem aktuellen Abo nicht freigeschaltet.",
                            "feature_gating": True,
                            "entitlements": entitlements,
                        }
                    ),
                    403,
                )

        result = execute_search(
            payload,
            request.host_url,
            request.files.get("image"),
        )
        if billing_enabled():
            result["entitlements"] = entitlements
        return jsonify(result)
    except SearchValidationError as error:
        return jsonify({"errors": error.errors}), 400


@search_bp.route("/api/reverse-image/<token>", methods=["GET"])
def reverse_image_asset(token):
    try:
        image_path, mime_type = resolve_uploaded_image(token)
        return send_file(image_path, mimetype=mime_type, conditional=True, max_age=300)
    except SearchValidationError:
        return jsonify({"error": "Der Reverse-Image-Link ist ungueltig oder abgelaufen."}), 404
