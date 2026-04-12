
# --- Imports & Blueprint-Definition ganz oben ---
from flask import Blueprint, request, jsonify, abort, session
from app.extensions.main import db
from app.models import LiveStream, LiveLike, LiveChatMessage, LiveGift, User
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from app.services.provider_adapter import get_provider_adapter, ProviderError

live_api_v2_bp = Blueprint("live_api_v2", __name__)

# --- Provider-Integration ---
@live_api_v2_bp.route("/api/live/streams", methods=["GET"])
def list_streams():
    streams = LiveStream.query.order_by(LiveStream.created_at.desc()).all()
    return jsonify([
        {
            "id": s.id,
            "title": s.title,
            "provider": s.provider,
            "provider_input_id": s.provider_input_id,
            "provider_channel_id": s.provider_channel_id,
            "ingest_url": s.ingest_url,
            "playback_url": s.playback_url,
            "provider_status": s.provider_status,
            "provider_output_bucket": s.provider_output_bucket,
            "location": s.location,
            "stream_key": s.stream_key,
            "created_at": s.created_at.isoformat(),
        }
        for s in streams
    ])

@live_api_v2_bp.route("/api/live/streams/<int:stream_id>", methods=["GET"])
def get_stream_provider(stream_id):
    stream = LiveStream.query.get(stream_id)
    if not stream:
        abort(404)
    result = {
        "id": stream.id,
        "title": stream.title,
        "provider": stream.provider,
        "provider_input_id": stream.provider_input_id,
        "provider_channel_id": stream.provider_channel_id,
        "ingest_url": stream.ingest_url,
        "playback_url": stream.playback_url,
        "provider_status": stream.provider_status,
        "provider_output_bucket": stream.provider_output_bucket,
        "location": stream.location,
        "stream_key": stream.stream_key,
        "created_at": stream.created_at.isoformat(),
    }
    # Provider-Status live abfragen
    if stream.provider and stream.provider_channel_id:
        adapter = get_provider_adapter(stream.provider)
        if adapter:
            try:
                status = adapter.get_stream_status(stream.provider_channel_id)
                result["provider_status_detail"] = status
            except ProviderError as exc:
                result["provider_status_error"] = exc.as_dict()
    return jsonify(result)

@live_api_v2_bp.route("/api/live/streams/<int:stream_id>/start", methods=["POST"])
def start_stream(stream_id):
    stream = LiveStream.query.get(stream_id)
    if not stream:
        abort(404)
    if stream.provider_status not in ("draft", "error"):
        return jsonify({"success": False, "error": "Stream kann nur aus draft/error gestartet werden."}), 400
    provider = (stream.provider or "google").lower()
    adapter = get_provider_adapter(provider)
    if not adapter:
        return jsonify({"success": False, "error": f"Provider {provider} nicht verfügbar."}), 400
    try:
        meta = {
            "title": stream.title,
            "category": stream.category,
            "game": stream.game,
            "tags": stream.tags,
            "location": stream.location,
            "output_bucket": stream.provider_output_bucket,
        }
        result = adapter.create_stream(meta)
        stream.provider = provider
        stream.provider_input_id = result.get("provider_input_id")
        stream.provider_channel_id = result.get("provider_channel_id")
        stream.ingest_url = result.get("ingest_url")
        stream.playback_url = result.get("playback_url")
        stream.stream_key = result.get("stream_key")
        stream.provider_status = result.get("provider_status") or "provisioning"
        db.session.commit()
        return jsonify({"success": True, "stream_id": stream.id, "provider": provider, "details": result})
    except ProviderError as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": exc.as_dict()}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400

@live_api_v2_bp.route("/api/live/streams/<int:stream_id>/end", methods=["POST"])
def end_stream(stream_id):
    stream = LiveStream.query.get(stream_id)
    if not stream:
        abort(404)
    if not stream.provider or not stream.provider_channel_id:
        return jsonify({"success": False, "error": "Kein aktiver Provider-Stream."}), 400
    adapter = get_provider_adapter(stream.provider)
    if not adapter:
        return jsonify({"success": False, "error": f"Provider {stream.provider} nicht verfügbar."}), 400
    try:
        result = adapter.stop_stream(stream.provider_channel_id)
        stream.provider_status = "ended"
        db.session.commit()
        return jsonify({"success": True, "details": result})
    except ProviderError as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": exc.as_dict()}), 400
    except Exception as exc:
        db.session.rollback()
        return jsonify({"success": False, "error": str(exc)}), 400

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
    from app.extensions.main import db
    stream = db.session.get(LiveStream, stream_id)
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
