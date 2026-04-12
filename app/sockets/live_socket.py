
        message = (data.get("message") or "").strip()

# --- Funktionsbasierte Handler ---
from app.extensions.socketio import socketio

def get_room(stream_id):
    return f"stream_{stream_id}"

viewer_counts = {}
like_counts = {}

@socketio.on("join_stream", namespace="/live")
def handle_join_stream(data):
    stream_id = (data or {}).get("stream_id")
    if not stream_id:
        return
    room = get_room(stream_id)
    join_room(room)
    viewer_counts[stream_id] = viewer_counts.get(stream_id, 0) + 1
    emit(
        "viewer_update",
        {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]},
        to=room,
        namespace="/live",
    )

@socketio.on("leave_stream", namespace="/live")
def handle_leave_stream(data):
    stream_id = (data or {}).get("stream_id")
    if not stream_id:
        return
    room = get_room(stream_id)
    leave_room(room)
    viewer_counts[stream_id] = max(0, viewer_counts.get(stream_id, 0) - 1)
    emit(
        "viewer_update",
        {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]},
        to=room,
        namespace="/live",
    )

@socketio.on("send_message", namespace="/live")
def handle_send_message(data):
    data = data or {}
    stream_id = data.get("stream_id")
    message = (data.get("message") or "").strip()
    username = (data.get("username") or "Anonymous").strip()
    if not stream_id or not message:
        return
    room = get_room(stream_id)
    emit(
        "new_message",
        {"stream_id": stream_id, "username": username, "message": message},
        to=room,
        namespace="/live",
    )

@socketio.on("send_like", namespace="/live")
def handle_send_like(data):
    data = data or {}
    stream_id = data.get("stream_id")
    if not stream_id:
        return
    room = get_room(stream_id)
    like_counts[stream_id] = like_counts.get(stream_id, 0) + 1
    emit(
        "new_like",
        {"stream_id": stream_id, "likes": like_counts[stream_id]},
        to=room,
        namespace="/live",
    )

@socketio.on("send_gift", namespace="/live")
def handle_send_gift(data):
    data = data or {}
    stream_id = data.get("stream_id")
    gift_type = data.get("gift_type") or "unknown"
    amount = data.get("amount") or 1
    username = (data.get("username") or "Anonymous").strip()
    if not stream_id:
        return
    room = get_room(stream_id)
    emit(
        "new_gift",
        {
            "stream_id": stream_id,
            "gift_type": gift_type,
            "amount": amount,
            "username": username,
        },
        to=room,
        namespace="/live",
    )

        username = data.get("username", "testuser")
    # Import triggers handler registration
    pass
        if not user_id or not validate_stream_id(stream_id) or not validate_message(message):
            return
        if rate_limited(sid, "send_message", 5, 10):
            emit("rate_limit", {"event": "send_message", "msg": "Zu viele Nachrichten. Bitte warte kurz."}, namespace="/live")
            return
        payload = {"stream_id": stream_id, "username": username, "message": message}
        room = get_stream_room(stream_id)
        emit("new_message", payload, room=room, namespace="/live")

    def on_send_like(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        user_id = session.get("user_id") or data.get("user_id")
        if not user_id or not validate_stream_id(stream_id):
            return
        if rate_limited(sid, "send_like", 5, 10):
            emit("rate_limit", {"event": "send_like", "msg": "Zu viele Likes. Bitte warte kurz."}, namespace="/live")
            return
        # Like-Count erhöhen (optional, für Demo)
        if not hasattr(self, "_like_counts"):
            self._like_counts = {}
        self._like_counts[stream_id] = self._like_counts.get(stream_id, 0) + 1
        payload = {"stream_id": stream_id, "likes": self._like_counts[stream_id]}
        room = get_stream_room(stream_id)
        emit("new_like", payload, room=room, namespace="/live")

    def on_send_gift(self, data):
        stream_id = data.get("stream_id")
        gift_type = data.get("gift_type")
        amount = data.get("amount")
        sid = request.sid
        user_id = session.get("user_id") or data.get("user_id")
        username = data.get("username", "testuser")
        if not user_id or not validate_stream_id(stream_id) or not validate_gift_type(gift_type) or not validate_amount(amount):
            return
        if rate_limited(sid, "send_gift", 3, 20):
            emit("rate_limit", {"event": "send_gift", "msg": "Zu viele Gifts. Bitte warte kurz."}, namespace="/live")
            return
        payload = {"stream_id": stream_id, "gift_type": gift_type, "amount": int(amount), "username": username}
        room = get_stream_room(stream_id)
        emit("new_gift", payload, room=room, namespace="/live")

    def on_leaderboard_update(self, data):
        stream_id = data.get("stream_id")
        room = get_stream_room(stream_id)
        emit("leaderboard_update", {"stream_id": stream_id, "leaderboard": []}, room=room)

    def on_stream_state_update(self, data):
        stream_id = data.get("stream_id")
        state = data.get("state")
        room = get_stream_room(stream_id)
        emit("stream_state_update", {"stream_id": stream_id, "state": state}, room=room)

def init_app(app):
    socketio = app.socketio
    socketio.on_namespace(LiveNamespace("/live"))
