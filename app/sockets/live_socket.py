from flask import session
from flask_socketio import join_room, leave_room, emit
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
