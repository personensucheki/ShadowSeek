from flask_socketio import SocketIO
import os

# SocketIO-Objekt zentral, Redis-ready
def create_socketio(app=None):
    cors_origins = app.config.get("SOCKETIO_CORS_ORIGINS", "*") if app else "*"
    async_mode = app.config.get("SOCKETIO_ASYNC_MODE", "eventlet") if app else "eventlet"
    message_queue = None
    redis_url = os.environ.get("REDIS_URL") or app.config.get("REDIS_URL") if app else None
    if redis_url:
        message_queue = redis_url
    return SocketIO(
        app,
        cors_allowed_origins=cors_origins,
        async_mode=async_mode,
        message_queue=message_queue,
        logger=True,
        engineio_logger=True,
    )
