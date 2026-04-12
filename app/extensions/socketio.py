from flask_socketio import SocketIO

# SocketIO-Objekt zentral, damit später Redis etc. ergänzt werden kann
def create_socketio(app=None):
    return SocketIO(
        app,
        cors_allowed_origins="*",  # Für MVP, später ggf. restriktiver
        async_mode="eventlet",     # Oder "gevent"/"threading" je nach Deployment
        logger=True,
        engineio_logger=True,
    )
