from app import create_app

app = create_app()
socketio = app.socketio

if __name__ == "__main__":
    # Für MVP: eventlet/gevent kann später konfiguriert werden
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
