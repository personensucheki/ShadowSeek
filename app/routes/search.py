from importlib import import_module

from flask import Blueprint, jsonify, render_template, request, send_file, session

from ..services.search_service import (
    PLATFORM_INDEX,
    SearchValidationError,
    build_search_payload,
    execute_search,
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

def _billing_helpers():
    try:
        runtime_module = import_module("app.py")
    except ModuleNotFoundError:
        runtime_module = None
    except Exception:
        runtime_module = None

    get_customer = getattr(runtime_module, "get_customer_record_by_user_id", None) if runtime_module else None
    get_entitlements = getattr(runtime_module, "get_plan_entitlements", None) if runtime_module else None

    if callable(get_customer) and callable(get_entitlements):
        return get_customer, get_entitlements

    default_platforms = list(PLATFORM_INDEX.keys())

    def _default_get_customer_record_by_user_id(_user_id):
        return None

    def _default_get_plan_entitlements(_plan_code):
        return {
            "enabled_platforms": default_platforms,
            "deepsearch_allowed": True,
        }

    return _default_get_customer_record_by_user_id, _default_get_plan_entitlements

@search_bp.route("/api/search", methods=["POST"])
def api_search():
    try:
        payload = build_search_payload(request.form)
        get_customer_record_by_user_id, get_plan_entitlements = _billing_helpers()
        user_id = session.get("user_id")
        entitlements = get_plan_entitlements(None)
        if user_id:
            row = get_customer_record_by_user_id(user_id)
            if row:
                entitlements = get_plan_entitlements(row["plan_code"])
        # Feature-Gating: Prüfe alle angefragten Plattformen
        for platform in payload.platforms:
            if platform not in entitlements["enabled_platforms"]:
                print(f"[Feature-Gating] User {user_id} hat keinen Zugriff auf Plattform: {platform}")
                return jsonify({
                    "error": f"Dein aktuelles Abo erlaubt keine Suche auf: {platform}.",
                    "required": entitlements["enabled_platforms"],
                    "missing": platform,
                    "feature_gating": True
                }), 403
        result = execute_search(
            payload,
            request.host_url,
            request.files.get("image"),
        )
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
