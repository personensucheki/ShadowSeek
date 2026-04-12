import os
from flask_socketio import SocketIO

# Globales SocketIO-Objekt, wird in App-Factory initialisiert
socketio = SocketIO()

def init_socketio(app):
    cors_origins = app.config.get("SOCKETIO_CORS_ORIGINS", "*")
    async_mode = os.environ.get("SOCKETIO_ASYNC_MODE", "threading")
    message_queue = None
    redis_url = os.environ.get("REDIS_URL") or app.config.get("REDIS_URL")
    if redis_url:
        message_queue = redis_url
    socketio.init_app(
        app,
        cors_allowed_origins=cors_origins,
        async_mode=async_mode,
        message_queue=message_queue,
        logger=True,
        engineio_logger=True,
    )
