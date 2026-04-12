
# --- Imports & Konstanten ---
from flask import session, request
from flask_socketio import join_room, leave_room, emit, Namespace
from collections import defaultdict
import time

# --- In-Memory Daten (MVP, später Redis) ---
viewer_counts = defaultdict(int)
socket_stream_map = {}

STREAM_ROOM_PREFIX = "stream_"

# --- Hilfsfunktionen ---
def get_stream_room(stream_id):
    return f"{STREAM_ROOM_PREFIX}{stream_id}"

def handle_join_stream(socketio, sid, stream_id):
    room = get_stream_room(stream_id)
    join_room(room, sid=sid)
    viewer_counts[stream_id] += 1
    if viewer_counts[stream_id] < 1:
        viewer_counts[stream_id] = 1
    socketio.emit("viewer_update", {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]}, room=room)

def handle_leave_stream(socketio, sid, stream_id):
    room = get_stream_room(stream_id)
    leave_room(room, sid=sid)
    viewer_counts[stream_id] = max(0, viewer_counts[stream_id] - 1)
    socketio.emit("viewer_update", {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]}, room=room)

def validate_stream_id(stream_id):
    return stream_id and isinstance(stream_id, str) and len(stream_id) <= 64

def validate_message(msg):
    return msg and isinstance(msg, str) and 0 < len(msg) <= 500

def validate_gift_type(gift_type):
    return gift_type and isinstance(gift_type, str) and len(gift_type) <= 32

def validate_amount(amount):
    try:
        amt = int(amount)
        return 1 <= amt <= 100
    except Exception:
        return False

# --- Rate-Limit-Logik ---
_rate_limits = defaultdict(lambda: defaultdict(list))
def rate_limited(sid, event, max_calls, per_seconds):
    now = time.time()
    timestamps = _rate_limits[sid][event]
    _rate_limits[sid][event] = [t for t in timestamps if now - t < per_seconds]
    if len(_rate_limits[sid][event]) >= max_calls:
        return True
    _rate_limits[sid][event].append(now)
    return False

class LiveNamespace(Namespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_join_stream(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        if not validate_stream_id(stream_id):
            return
        handle_join_stream(self.server, sid, stream_id)
        socket_stream_map[sid] = stream_id

    def on_leave_stream(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        if not validate_stream_id(stream_id):
            return
        handle_leave_stream(self.server, sid, stream_id)
        socket_stream_map.pop(sid, None)

    def on_send_message(self, data):
        stream_id = data.get("stream_id")
        message = (data.get("message") or "").strip()
        sid = request.sid
        user_id = session.get("user_id")
        if not user_id or not validate_stream_id(stream_id) or not validate_message(message):
            return
        if rate_limited(sid, "send_message", 5, 10):
            emit("rate_limit", {"event": "send_message", "msg": "Zu viele Nachrichten. Bitte warte kurz."})
            return
        payload = {"stream_id": stream_id, "user_id": user_id, "message": message}
        room = get_stream_room(stream_id)
        emit("new_message", payload, room=room)

    def on_send_like(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        user_id = session.get("user_id")
        if not user_id or not validate_stream_id(stream_id):
            return
        if rate_limited(sid, "send_like", 5, 10):
            emit("rate_limit", {"event": "send_like", "msg": "Zu viele Likes. Bitte warte kurz."})
            return
        payload = {"stream_id": stream_id, "user_id": user_id}
        room = get_stream_room(stream_id)
        emit("new_like", payload, room=room)

    def on_send_gift(self, data):
        stream_id = data.get("stream_id")
        gift_type = data.get("gift_type")
        amount = data.get("amount")
        sid = request.sid
        user_id = session.get("user_id")
        if not user_id or not validate_stream_id(stream_id) or not validate_gift_type(gift_type) or not validate_amount(amount):
            return
        if rate_limited(sid, "send_gift", 3, 20):
            emit("rate_limit", {"event": "send_gift", "msg": "Zu viele Gifts. Bitte warte kurz."})
            return
        payload = {"stream_id": stream_id, "user_id": user_id, "gift_type": gift_type, "amount": int(amount)}
        room = get_stream_room(stream_id)
        emit("new_gift", payload, room=room)

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
