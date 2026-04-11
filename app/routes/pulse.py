from flask import Blueprint, request, jsonify
from app.services.pulse_service import search_creator_service

bp = Blueprint("pulse", __name__)

@bp.route("/api/pulse/search", methods=["POST"])
def pulse_search():
    try:
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        platform = data.get("platform", "").strip().lower()
        realname = data.get("realname", "").strip() if data.get("realname") else None
        deepsearch = bool(data.get("deepsearch", False))
        if not username or not platform:
            return jsonify({"success": False, "error": "username und platform sind Pflichtfelder."}), 400
        result = search_creator_service(username, platform, realname, deepsearch)
        return jsonify({
            "success": True,
            "query": {
                "username": username,
                "platform": platform,
                "realname": realname or "",
                "deepsearch": deepsearch
            },
            **result
        })
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as ex:
        return jsonify({"success": False, "error": "Internal error: " + str(ex)}), 500
