from pathlib import Path

from flask import Flask, jsonify, request
from werkzeug.exceptions import RequestEntityTooLarge

from .extensions import csrf, db, migrate


def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=True)

    if config_class:
        app.config.from_object(config_class)
    else:
        from .config import DevConfig

        app.config.from_object(DevConfig)

    upload_directory = app.config.get("UPLOAD_DIRECTORY")
    if not upload_directory:
        upload_directory = Path(app.instance_path) / "uploads"
        app.config["UPLOAD_DIRECTORY"] = str(upload_directory)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_DIRECTORY"]).mkdir(parents=True, exist_ok=True)

    if not app.config.get("SECRET_KEY") and not app.config.get("TESTING"):
        raise RuntimeError("SECRET_KEY must be configured for ShadowSeek.")

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf

        return {"csrf_token": generate_csrf()}

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Die hochgeladene Datei ist zu gross."}), 413
        return error, 413

    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.chatbot import chatbot_bp
    from .routes.health import health_bp
    from .routes.search import search_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(chatbot_bp)

    return app
