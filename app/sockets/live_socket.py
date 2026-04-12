from flask import session, request
from flask_socketio import join_room, leave_room, emit, Namespace
from collections import defaultdict

# In-Memory Viewer-Count pro Stream (MVP, später Redis)
viewer_counts = defaultdict(int)

# Room-Name-Konvention
STREAM_ROOM_PREFIX = "stream_"
def get_stream_room(stream_id):
    return f"{STREAM_ROOM_PREFIX}{stream_id}"

# Join-Handler

def handle_join_stream(socketio, sid, stream_id):
    room = get_stream_room(stream_id)
    join_room(room, sid=sid)
    viewer_counts[stream_id] += 1
    # Schutz gegen negatives Zählen
    if viewer_counts[stream_id] < 1:
        viewer_counts[stream_id] = 1
    # Broadcast neuen Viewer-Count
    socketio.emit("viewer_update", {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]}, room=room)

# Leave-Handler

def handle_leave_stream(socketio, sid, stream_id):
    room = get_stream_room(stream_id)
    leave_room(room, sid=sid)
    viewer_counts[stream_id] = max(0, viewer_counts[stream_id] - 1)
    socketio.emit("viewer_update", {"stream_id": stream_id, "viewer_count": viewer_counts[stream_id]}, room=room)

# --- Verbesserte Viewer-Count-Logik ---
# Merkt sich, welche Sockets in welchem Stream sind
socket_stream_map = {}


# --- Einfache Rate-Limit- und Validierungsbasis ---
import time

class LiveNamespace(Namespace):
    # In-Memory Rate-Limit: {sid: {event: [timestamps]}}
    rate_limits = defaultdict(lambda: defaultdict(list))

    def _rate_limited(self, sid, event, max_calls, per_seconds):
        now = time.time()
        timestamps = self.rate_limits[sid][event]
        # Entferne alte Einträge
        self.rate_limits[sid][event] = [t for t in timestamps if now - t < per_seconds]
        if len(self.rate_limits[sid][event]) >= max_calls:
            return True
        self.rate_limits[sid][event].append(now)
        return False

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_join_stream(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        # Validierung: Stream-ID Pflicht, max. 64 Zeichen
        if not stream_id or not isinstance(stream_id, str) or len(stream_id) > 64:
            return
        handle_join_stream(self.server, sid, stream_id)
        self.socket_stream_map[sid] = stream_id

    def on_leave_stream(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        if not stream_id or not isinstance(stream_id, str) or len(stream_id) > 64:
            return
        handle_leave_stream(self.server, sid, stream_id)
        self.socket_stream_map.pop(sid, None)

    def on_send_message(self, data):
        stream_id = data.get("stream_id")
        message = (data.get("message") or "").strip()
        sid = request.sid
        user_id = session.get("user_id")
        # Session-Check: Nur eingeloggte User
        if not user_id:
            return
        # Validierung
        if not stream_id or not isinstance(stream_id, str) or len(stream_id) > 64:
            return
        if not message or len(message) > 500:
            return
        # Rate-Limit: max 5 Nachrichten pro 10s
        if self._rate_limited(sid, "send_message", 5, 10):
            emit("rate_limit", {"event": "send_message", "msg": "Zu viele Nachrichten. Bitte warte kurz."})
            return
        payload = {
            "stream_id": stream_id,
            "user_id": user_id,
            "message": message,
        }
        room = get_stream_room(stream_id)
        emit("new_message", payload, room=room)

    def on_send_like(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        user_id = session.get("user_id")
        if not user_id:
            return
        if not stream_id or not isinstance(stream_id, str) or len(stream_id) > 64:
            return
        # Rate-Limit: max 5 Likes pro 10s
        if self._rate_limited(sid, "send_like", 5, 10):
            emit("rate_limit", {"event": "send_like", "msg": "Zu viele Likes. Bitte warte kurz."})
            return
        payload = {
            "stream_id": stream_id,
            "user_id": user_id,
        }
        room = get_stream_room(stream_id)
        emit("new_like", payload, room=room)

    def on_send_gift(self, data):
        stream_id = data.get("stream_id")
        gift_type = data.get("gift_type")
        try:
            amount = int(data.get("amount") or 1)
        except Exception:
            amount = 1
        sid = request.sid
        user_id = session.get("user_id")
        if not user_id:
            return
        if not stream_id or not isinstance(stream_id, str) or len(stream_id) > 64:
            return
        if not gift_type or not isinstance(gift_type, str) or len(gift_type) > 32:
            return
        if amount < 1 or amount > 100:
            return
        # Rate-Limit: max 3 Gifts pro 20s
        if self._rate_limited(sid, "send_gift", 3, 20):
            emit("rate_limit", {"event": "send_gift", "msg": "Zu viele Gifts. Bitte warte kurz."})
            return
        payload = {
            "stream_id": stream_id,
            "user_id": user_id,
            "gift_type": gift_type,
            "amount": amount,
        }
        room = get_stream_room(stream_id)
        emit("new_gift", payload, room=room)

    # Leaderboard-Update (Platzhalter, später DB)
    def on_leaderboard_update(self, data):
        stream_id = data.get("stream_id")
        room = get_stream_room(stream_id)
        emit("leaderboard_update", {"stream_id": stream_id, "leaderboard": []}, room=room)

    # Stream-State-Update (Platzhalter)
    def on_stream_state_update(self, data):
        stream_id = data.get("stream_id")
        state = data.get("state")
        room = get_stream_room(stream_id)
        emit("stream_state_update", {"stream_id": stream_id, "state": state}, room=room)

def init_app(app):
    socketio = app.socketio
    socketio.on_namespace(LiveNamespace("/live"))
