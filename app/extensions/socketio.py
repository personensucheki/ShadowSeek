from flask_socketio import SocketIO

# SocketIO-Objekt zentral, damit später Redis etc. ergänzt werden kann
def create_socketio(app=None):
    # Für MVP: alle Origins erlauben, später z.B. ["https://shadowseek.app"]
    cors_origins = app.config.get("SOCKETIO_CORS_ORIGINS", "*") if app else "*"
    return SocketIO(
        app,
        cors_allowed_origins=cors_origins,
        async_mode="eventlet",  # Oder "gevent"/"threading" je nach Deployment
        logger=True,
        engineio_logger=True,
    )
