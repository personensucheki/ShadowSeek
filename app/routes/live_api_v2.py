from flask import Blueprint, request, jsonify, abort, session
from app.extensions import db
from app.models import LiveStream, LiveLike, LiveChatMessage, LiveGift, User
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

live_api_v2_bp = Blueprint("live_api_v2", __name__)

# Stream anlegen
@live_api_v2_bp.route("/api/live/stream", methods=["POST"])
def create_stream():
    data = request.get_json(force=True)
    try:
        stream = LiveStream(
            title=data.get("title"),
            description=data.get("description"),
            category=data.get("category"),
            game=data.get("game"),
            tags=data.get("tags"),
            allow_gifts=bool(data.get("allow_gifts")),
        )
        db.session.add(stream)
        db.session.commit()
        return jsonify({"success": True, "stream_id": stream.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400

# Stream laden
@live_api_v2_bp.route("/api/live/stream/<int:stream_id>", methods=["GET"])
def get_stream(stream_id):
    stream = LiveStream.query.get(stream_id)
    if not stream:
        abort(404)
    return jsonify({
        "id": stream.id,
        "title": stream.title,
        "description": stream.description,
        "category": stream.category,
        "game": stream.game,
        "tags": stream.tags,
        "allow_gifts": stream.allow_gifts,
        "created_at": stream.created_at.isoformat(),
    })

# Like speichern
@live_api_v2_bp.route("/api/live/like", methods=["POST"])
def add_like():
    data = request.get_json(force=True)
    stream_id = data.get("stream_id")
    user_id = session.get("user_id") or data.get("user_id")
    if not stream_id or not user_id:
        return jsonify({"success": False, "error": "stream_id und user_id erforderlich"}), 400
    like = LiveLike(stream_id=stream_id, user_id=user_id)
    db.session.add(like)
    db.session.commit()
    return jsonify({"success": True})

# Chat-Nachricht speichern
@live_api_v2_bp.route("/api/live/chat", methods=["POST"])
def add_chat():
    data = request.get_json(force=True)
    stream_id = data.get("stream_id")
    user_id = session.get("user_id") or data.get("user_id")
    message = data.get("message")
    if not stream_id or not user_id or not message:
        return jsonify({"success": False, "error": "stream_id, user_id, message erforderlich"}), 400
    chat = LiveChatMessage(stream_id=stream_id, user_id=user_id, message=message)
    db.session.add(chat)
    db.session.commit()
    return jsonify({"success": True})

# Geschenke loggen
@live_api_v2_bp.route("/api/live/gift", methods=["POST"])
def add_gift():
    data = request.get_json(force=True)
    stream_id = data.get("stream_id")
    user_id = session.get("user_id") or data.get("user_id")
    gift_type = data.get("gift_type")
    amount = int(data.get("amount") or 1)
    if not stream_id or not user_id or not gift_type:
        return jsonify({"success": False, "error": "stream_id, user_id, gift_type erforderlich"}), 400
    gift = LiveGift(stream_id=stream_id, user_id=user_id, gift_type=gift_type, amount=amount)
    db.session.add(gift)
    db.session.commit()
    return jsonify({"success": True})

# Leaderboard
@live_api_v2_bp.route("/api/live/leaderboard/<int:stream_id>", methods=["GET"])
def leaderboard(stream_id):
    gifts = db.session.query(LiveGift.user_id, db.func.sum(LiveGift.amount).label("total")).filter_by(stream_id=stream_id).group_by(LiveGift.user_id).order_by(db.desc("total")).limit(10).all()
    users = User.query.filter(User.id.in_([g[0] for g in gifts])).all()
    user_map = {u.id: u for u in users}
    return jsonify({
        "results": [
            {"user_id": uid, "username": user_map.get(uid).username if user_map.get(uid) else None, "total": total}
            for uid, total in gifts
        ]
    })
