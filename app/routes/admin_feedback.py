from flask import Blueprint, render_template, request
from ..models.assistant_feedback import AssistantFeedback
from ..extensions import db

admin_feedback_bp = Blueprint("admin_feedback", __name__, url_prefix="/admin/feedback")

@admin_feedback_bp.route("/", methods=["GET"])
def feedback_overview():
    score = request.args.get("score")
    query = AssistantFeedback.query
    if score is not None:
        try:
            score = int(score)
            query = query.filter_by(feedback_score=score)
        except Exception:
            pass
    feedbacks = query.order_by(AssistantFeedback.created_at.desc()).limit(100).all()
    return render_template("admin_feedback.html", feedbacks=feedbacks)
