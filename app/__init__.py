import os
from pathlib import Path

from flask import Flask, jsonify, request, session
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import RequestEntityTooLarge

from .extensions import csrf, db, migrate


def _resolve_default_config():
    from .config import DevConfig, ProdConfig

    environment = (
        os.environ.get("SHADOWSEEK_ENV")
        or os.environ.get("FLASK_ENV")
        or os.environ.get("APP_ENV")
        or ""
    ).strip().lower()

    if environment in {"prod", "production"}:
        return ProdConfig

    if os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
        return ProdConfig

    return DevConfig


def create_app(config_class=None):
    app = Flask(__name__, instance_relative_config=True)

    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(_resolve_default_config())

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

    # Admin-Feedback-Blueprint registrieren
    from .routes.admin_feedback import admin_feedback_bp
    app.register_blueprint(admin_feedback_bp)


    @app.context_processor
    def inject_csrf_token_and_user():
        from flask_wtf.csrf import generate_csrf
        from app.models.user import User
        user_id = session.get("user_id")
        current_user = None
        if user_id:
            current_user = User.query.get(user_id)
        return {"csrf_token": generate_csrf(), "g": {'current_user': current_user}}

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Die hochgeladene Datei ist zu gross."}), 413
        return error, 413

    def _is_json_api_request():
        return request.path.startswith("/api/") or (
            request.path.startswith("/search/") and request.is_json
        )

    @app.errorhandler(Exception)
    def handle_unexpected_api_error(error):
        if isinstance(error, HTTPException):
            return error
        if _is_json_api_request():
            return jsonify({"success": False, "error": "Internal server error"}), 500
        raise error


    from .routes.admin import admin_bp
    from .routes.auth import auth_bp
    from .routes.chatbot import chatbot_bp
    from .routes.health import health_bp
    from .routes.search import search_bp
    from .routes.dashboard import dashboard_bp
    from .routes.export import export_bp
    from .routes.profile import profile_bp
    from .routes.analysis import analysis_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(analysis_bp)
    from .routes.einnahmen_api import api_bp
    app.register_blueprint(api_bp)
    from .routes.live_api import live_api_bp
    app.register_blueprint(live_api_bp)
    from .routes.query_api import query_api_bp
    app.register_blueprint(query_api_bp)

    return app
