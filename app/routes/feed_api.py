"""
API-Routen für Feed, Live und Interaktionen
"""
from flask import Blueprint, request, jsonify
from app.services.feed_service import feed_service
from app.services.live_service import live_service
from app.services.recommendation_service import recommendation_service
from app.services.ranking_service import ranking_service
from app.services.user_interest_service import user_interest_service
from app.models.event_tracking import FeedImpression, UserInteraction, LiveMetric
from app.extensions.main import db

feed_api_bp = Blueprint("feed_api", __name__)

@feed_api_bp.route("/api/feed", methods=["GET"])
def get_feed():
    user_id = request.args.get("user_id")
    feed_type = request.args.get("type", "discovery")
    location = request.args.get("location")
    posts = feed_service.get_feed(user_id, feed_type, location)
    return jsonify({"success": True, "items": posts})

@feed_api_bp.route("/api/live/recommended", methods=["GET"])
def get_live_recommended():
    user_id = request.args.get("user_id")
    lives = live_service.get_recommended_live(user_id)
    return jsonify({"success": True, "items": lives})

@feed_api_bp.route("/api/interactions/feed", methods=["POST"])
def post_feed_interaction():
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    post_id = data.get("post_id")
    event_type = data.get("event_type")
    value = data.get("value")
    meta = data.get("meta")
    if not (user_id and post_id and event_type):
        return jsonify({"success": False, "error": "Missing required fields."}), 400
    interaction = UserInteraction(user_id=user_id, post_id=post_id, event_type=event_type, value=value, meta=meta)
    db.session.add(interaction)
    db.session.commit()
    user_interest_service.update_user_interest_profile(user_id, interaction)
    return jsonify({"success": True})

@feed_api_bp.route("/api/interactions/live", methods=["POST"])
def post_live_interaction():
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    live_session_id = data.get("live_session_id")
    event_type = data.get("event_type")
    value = data.get("value")
    meta = data.get("meta")
    if not (user_id and live_session_id and event_type):
        return jsonify({"success": False, "error": "Missing required fields."}), 400
    metric = LiveMetric(user_id=user_id, live_session_id=live_session_id, event_type=event_type, value=value, meta=meta)
    db.session.add(metric)
    db.session.commit()
    return jsonify({"success": True})
