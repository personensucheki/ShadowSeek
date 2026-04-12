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

class LiveNamespace(Namespace):
    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def on_join_stream(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        if stream_id:
            handle_join_stream(self.server, sid, stream_id)

    def on_leave_stream(self, data):
        stream_id = data.get("stream_id")
        sid = request.sid
        if stream_id:
            handle_leave_stream(self.server, sid, stream_id)

    def on_send_message(self, data):
        stream_id = data.get("stream_id")
        message = (data.get("message") or "").strip()
        sid = request.sid
        user_id = session.get("user_id")
        # Validierung
        if not stream_id or not message or len(message) > 500:
            return
        # Hier könnte DB-Speicherung erfolgen
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
        if not stream_id:
            return
        # Hier könnte Like in DB gespeichert werden
        payload = {
            "stream_id": stream_id,
            "user_id": user_id,
        }
        room = get_stream_room(stream_id)
        emit("new_like", payload, room=room)

    def on_send_gift(self, data):
        stream_id = data.get("stream_id")
        gift_type = data.get("gift_type")
        amount = int(data.get("amount") or 1)
        sid = request.sid
        user_id = session.get("user_id")
        if not stream_id or not gift_type or amount < 1:
            return
        # Hier könnte Gift in DB gespeichert werden
        payload = {
            "stream_id": stream_id,
            "user_id": user_id,
            "gift_type": gift_type,
            "amount": amount,
        }
        room = get_stream_room(stream_id)
        emit("new_gift", payload, room=room)

def init_app(app):
    socketio = app.socketio
    socketio.on_namespace(LiveNamespace("/live"))
