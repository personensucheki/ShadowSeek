from flask import Blueprint, jsonify, request


chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")


@chatbot_bp.route("", methods=["POST"])
def assistant_reply():
    request.get_json(silent=True)

    return jsonify(
        {
            "error": (
                "ShadowSeek Assistant ist noch nicht konfiguriert. "
                "Die Profilsuche bleibt aktiv, der Chat ist derzeit nur abgesichert."
            )
        }
    ), 503
