from __future__ import annotations

from flask_socketio import emit, join_room, leave_room

from app.extensions.socketio import socketio

viewer_counts: dict[str, int] = {}
like_counts: dict[str, int] = {}


def _room(stream_id: str) -> str:
    return f"stream_{stream_id}"


@socketio.on("join_stream", namespace="/live")
def handle_join_stream(data):
    stream_id = str((data or {}).get("stream_id") or "").strip()
    if not stream_id:
        return
    room = _room(stream_id)
    join_room(room)
    viewer_counts[stream_id] = viewer_counts.get(stream_id, 0) + 1
    emit(
        "viewer_update",
        {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]},
        to=room,
    )


@socketio.on("leave_stream", namespace="/live")
def handle_leave_stream(data):
    stream_id = str((data or {}).get("stream_id") or "").strip()
    if not stream_id:
        return
    room = _room(stream_id)
    leave_room(room)
    viewer_counts[stream_id] = max(0, viewer_counts.get(stream_id, 0) - 1)
    emit(
        "viewer_update",
        {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]},
        to=room,
    )


@socketio.on("send_message", namespace="/live")
def handle_send_message(data):
    payload = data or {}
    stream_id = str(payload.get("stream_id") or "").strip()
    message = str(payload.get("message") or "").strip()
    username = str(payload.get("username") or "Anonymous").strip() or "Anonymous"
    if not stream_id or not message:
        return
    emit(
        "new_message",
        {"stream_id": stream_id, "username": username, "message": message},
        to=_room(stream_id),
    )


@socketio.on("send_like", namespace="/live")
def handle_send_like(data):
    stream_id = str((data or {}).get("stream_id") or "").strip()
    if not stream_id:
        return
    like_counts[stream_id] = like_counts.get(stream_id, 0) + 1
    emit(
        "new_like",
        {"stream_id": stream_id, "likes": like_counts[stream_id]},
        to=_room(stream_id),
    )


@socketio.on("send_gift", namespace="/live")
def handle_send_gift(data):
    payload = data or {}
    stream_id = str(payload.get("stream_id") or "").strip()
    gift_type = str(payload.get("gift_type") or "unknown").strip() or "unknown"
    amount = int(payload.get("amount") or 1)
    username = str(payload.get("username") or "Anonymous").strip() or "Anonymous"
    if not stream_id:
        return
    emit(
        "new_gift",
        {
            "stream_id": stream_id,
            "gift_type": gift_type,
            "amount": amount,
            "username": username,
        },
        to=_room(stream_id),
    )


def register_live_socket_handlers(app=None):
    """Handlers are registered via decorators on import; keep hook for app startup."""
    return None


def init_app(app=None):
    """Backwards-compatible alias used by `app.create_app()`."""
    return register_live_socket_handlers(app)

