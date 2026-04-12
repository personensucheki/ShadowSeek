
from app.models.post_interaction import PostComment

# Kommentare listen
@feed_api_bp.route("/api/feed/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    post = MediaPost.query.get(post_id)
    if not post:
        return jsonify({"success": False, "error": {"message": "Post nicht gefunden.", "code": "not_found"}}), 404
    comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at.asc()).all()
    items = []
    for c in comments:
        user = User.query.get(c.user_id)
        items.append({
            "id": c.id,
            "user_id": c.user_id,
            "username": user.username if user else "user",
            "display_name": (user.display_name or user.username) if user else "User",
            "content": c.content,
            "created_at": c.created_at.isoformat(),
        })
    return jsonify({"success": True, "items": items})

# Kommentar erstellen
@feed_api_bp.route("/api/feed/<int:post_id>/comments", methods=["POST"])
def post_comment(post_id):
    user_id = session.get("user_id") or (request.json and request.json.get("user_id"))
    if not user_id:
        return jsonify({"success": False, "error": {"message": "Nicht eingeloggt.", "code": "not_authenticated"}}), 401
    post = MediaPost.query.get(post_id)
    if not post:
        return jsonify({"success": False, "error": {"message": "Post nicht gefunden.", "code": "not_found"}}), 404
    data = request.get_json(force=True)
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"success": False, "error": {"message": "Kommentar darf nicht leer sein.", "code": "empty"}}), 400
    comment = PostComment(post_id=post_id, user_id=user_id, content=content)
    db.session.add(comment)
    db.session.commit()
    user = User.query.get(user_id)
    return jsonify({
        "success": True,
        "comment": {
            "id": comment.id,
            "user_id": user_id,
            "username": user.username if user else "user",
            "display_name": (user.display_name or user.username) if user else "User",
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
        }
    })

# --- Interaktions- und View-Tracking-API ---

from flask import session
from app.models.post_interaction import PostLike
from app.models.media_post import MediaPost
from app.models import User

@feed_api_bp.route("/api/feed/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    user_id = session.get("user_id") or (request.json and request.json.get("user_id"))
    if not user_id:
        return jsonify({"success": False, "error": {"message": "Nicht eingeloggt.", "code": "not_authenticated"}}), 401
    post = MediaPost.query.get(post_id)
    if not post:
        return jsonify({"success": False, "error": {"message": "Post nicht gefunden.", "code": "not_found"}}), 404
    like = PostLike.query.filter_by(post_id=post_id, user_id=user_id).first()
    liked = False
    if like:
        db.session.delete(like)
        liked = False
    else:
        db.session.add(PostLike(post_id=post_id, user_id=user_id))
        liked = True
    # Like-Count aktualisieren
    db.session.flush()
    like_count = PostLike.query.filter_by(post_id=post_id).count()
    post.like_count = like_count
    db.session.commit()
    return jsonify({"success": True, "liked": liked, "like_count": like_count, "post_id": post_id})

@feed_api_bp.route("/api/feed/<int:post_id>/view", methods=["POST"])
def view_post(post_id):
    # TODO: Echte View-Logik
    # Erwartet: { user_id: ... }
    return jsonify({"success": True, "viewed": True, "post_id": post_id})
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
    dev_fallback = request.args.get("dev_fallback") == "1"
    try:
        items = feed_service.get_feed(user_id, feed_type, location, dev_fallback)
        return jsonify({"success": True, "items": items})
    except Exception as exc:
        return jsonify({"success": False, "error": {"message": str(exc), "code": "feed_error"}}), 500

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
