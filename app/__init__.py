import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, jsonify, request, session
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import RequestEntityTooLarge

from .extensions import csrf, db, migrate
from .services.billing import build_configured_plans
from .services.owner_bootstrap import ensure_owner_account


def _configure_database_uri(app):
    # Runtime-Hinweis:
    # DATABASE_URL kommt in Produktion von Render.
    # Lokal in PowerShell nur testen, wenn $env:DATABASE_URL gesetzt wurde.
    uri = os.environ.get("DATABASE_URL")
    if uri:
        parsed = urlsplit(uri)
        redacted_uri = f"{parsed.scheme}://{parsed.hostname or 'unknown'}{parsed.path or ''}"
    else:
        redacted_uri = None
    print("DATABASE_URL:", redacted_uri)

    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    if uri and uri.startswith("postgresql://") and not uri.startswith("postgresql+"):
        uri = uri.replace("postgresql://", "postgresql+psycopg://", 1)

    if uri:
        app.config["SQLALCHEMY_DATABASE_URI"] = uri


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

    _configure_database_uri(app)
    app.config["PLANS"] = build_configured_plans(app.config)

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

    with app.app_context():
       from app.models.user import User

       db.create_all()

       ensure_owner_account(app)

    @app.before_request
    def track_member_presence():
        user_id = session.get("user_id")
        if not user_id:
            return None

        last_ping_raw = session.get("presence_ping_at")
        if last_ping_raw:
            try:
                last_ping = datetime.fromisoformat(last_ping_raw)
                if datetime.utcnow() - last_ping < timedelta(seconds=90):
                    return None
            except ValueError:
                pass

        from app.models.user import User

        user = User.query.get(user_id)
        if not user:
            return None

        user.last_seen_at = datetime.utcnow()
        db.session.commit()
        session["presence_ping_at"] = datetime.utcnow().isoformat()
        return None

    @app.after_request
    def add_api_cors_headers(response):
        if request.path.startswith("/api/"):
            response.headers.setdefault("Access-Control-Allow-Origin", "*")
            response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-CSRFToken")
            response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        return response

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
        return {
            "csrf_token": generate_csrf(),
            "g": {"current_user": current_user},
            "billing_enabled": bool(app.config.get("BILLING_GATING_ENABLED")),
        }

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
    from .routes.community import community_bp
    from .routes.health import health_bp
    from .routes.search import search_bp
    from .routes.suggest import suggest_bp
    from .routes.websearch import websearch_bp
    from .routes.billing import billing_bp
    from .routes.dashboard import dashboard_bp
    from .routes.export import export_bp
    from .routes.profile import profile_bp
    from .routes.analysis import analysis_bp
    from .routes.pulse import bp as pulse_bp
    from .routes.oauth_connect import oauth_bp

    from .routes.live import live_bp
    from .routes.games_api import games_api_bp
    from .routes.live_api_v2 import live_api_v2_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(community_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(suggest_bp)
    app.register_blueprint(websearch_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(pulse_bp)
    app.register_blueprint(oauth_bp)
    app.register_blueprint(live_bp)
    app.register_blueprint(games_api_bp)
    app.register_blueprint(live_api_v2_bp)
    from .routes.einnahmen_api import api_bp
    app.register_blueprint(api_bp)
    from .routes.live_api import live_api_bp
    app.register_blueprint(live_api_bp)
    from .routes.query_api import query_api_bp
    app.register_blueprint(query_api_bp)

    return app
