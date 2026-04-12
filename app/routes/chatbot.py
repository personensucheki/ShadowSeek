
from flask import Blueprint, jsonify, request, current_app

from ..services.chatbot_service import ChatbotService
from ..models.assistant_feedback import AssistantFeedback
from app.extensions.main import db

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")

def get_search_context():
    # Hier könnte später echter Kontext aus Session/Persistenz geladen werden
    # Für Demo: Dummy-Kontext, falls im Request mitgesendet
    context = request.json.get("context") if request.is_json else None
    if context and isinstance(context, dict):
        return context
    return {}

@chatbot_bp.route("", methods=["POST"])
def assistant_reply():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "")
    context = get_search_context()

    # Hole OpenAI-Key aus Config, falls vorhanden
    openai_api_key = current_app.config.get("OPENAI_API_KEY")
    bot = ChatbotService(openai_api_key)

    try:
        reply = bot.handle_message(message, context)
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": "Assistant-Fehler: {}".format(str(e))}), 500


# Feedback-Endpoint: Speichert Feedback zu Bot-Antworten
import time
from flask import abort
from flask_wtf.csrf import validate_csrf, CSRFError
from werkzeug.exceptions import BadRequest
from flask import session

# Simple in-memory rate limit (per process, not distributed)
_feedback_rate_limit = {}
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX = 5     # max feedbacks per window per IP

def _rate_limit_check(ip):
    now = int(time.time())
    window = now // _RATE_LIMIT_WINDOW
    key = f"{ip}:{window}"
    count = _feedback_rate_limit.get(key, 0)
    if count >= _RATE_LIMIT_MAX:
        return False
    _feedback_rate_limit[key] = count + 1
    return True

def _validate_feedback_payload(data):
    if not isinstance(data, dict):
        raise BadRequest("Payload muss JSON-Objekt sein.")
    if not data.get("user_message") or not data.get("assistant_reply"):
        raise BadRequest("user_message und assistant_reply sind Pflichtfelder.")
    if "feedback_score" not in data:
        raise BadRequest("feedback_score fehlt.")
    try:
        int(data["feedback_score"])
    except Exception:
        raise BadRequest("feedback_score muss Zahl sein.")

@chatbot_bp.route("/feedback", methods=["POST"])
def assistant_feedback():
    # CSRF prüfen (Header oder Form)
    csrf_token = request.headers.get("X-CSRFToken") or request.form.get("csrf_token")
    try:
        if csrf_token:
            validate_csrf(csrf_token)
    except CSRFError:
        abort(400, "CSRF-Token ungültig oder fehlt.")

    # Rate-Limiting
    ip = request.remote_addr or "anon"
    if not _rate_limit_check(ip):
        abort(429, "Zu viele Feedbacks, bitte später erneut versuchen.")

    data = request.get_json(silent=True) or {}
    _validate_feedback_payload(data)

    user_message = data.get("user_message")
    assistant_reply = data.get("assistant_reply")
    search_context_json = data.get("search_context_json")
    feedback_score = data.get("feedback_score")
    intent_label = data.get("intent_label")
    resolved = data.get("resolved", False)

    fb = AssistantFeedback.create_safe(
        user_message=user_message,
        assistant_reply=assistant_reply,
        search_context_json=search_context_json,
        feedback_score=feedback_score,
        intent_label=intent_label,
        resolved=resolved,
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({"status": "ok"})
