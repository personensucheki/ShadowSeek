
from flask import Blueprint, jsonify, request, current_app

from ..services.chatbot_service import ChatbotService
from ..models.assistant_feedback import AssistantFeedback
from ..extensions import db

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
@chatbot_bp.route("/feedback", methods=["POST"])
def assistant_feedback():
    data = request.get_json(silent=True) or {}
    user_message = data.get("user_message")
    assistant_reply = data.get("assistant_reply")
    search_context_json = data.get("search_context_json")
    feedback_score = data.get("feedback_score")
    intent_label = data.get("intent_label")
    resolved = data.get("resolved", False)

    fb = AssistantFeedback(
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
