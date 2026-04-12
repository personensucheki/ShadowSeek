# app/helpers/factory.py

def register_blueprints(app):
    from app.routes.admin_feedback import admin_feedback_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.chatbot import chatbot_bp
    from app.routes.community import community_bp
    from app.routes.health import health_bp
    from app.routes.search import search_bp
    from app.routes.suggest import suggest_bp
    from app.routes.websearch import websearch_bp
    from app.routes.billing import billing_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.export import export_bp
    from app.routes.profile import profile_bp
    from app.routes.analysis import analysis_bp
    from app.routes.pulse import bp as pulse_bp
    from app.routes.oauth_connect import oauth_bp
    from app.routes.live import live_bp
    from app.routes.games_api import games_api_bp
    from app.routes.live_api_v2 import live_api_v2_bp
    from app.routes.einnahmen_api import api_bp
    from app.routes.live_api import live_api_bp
    from app.routes.query_api import query_api_bp
    from app.routes.feed import feed_bp

    app.register_blueprint(admin_feedback_bp)
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
    # live_api_v2_bp already defines routes under /api/live/...; do not double-prefix.
    app.register_blueprint(live_api_v2_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(live_api_bp)
    app.register_blueprint(query_api_bp)
    app.register_blueprint(feed_bp)


def register_hooks(app):
    from flask import session, request
    from datetime import datetime, timedelta
    from app.models.user import User
    from app.extensions.main import db

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
        user = db.session.get(User, user_id)
        if not user:
            return None
        user.last_seen_at = datetime.utcnow()
        db.session.commit()
        session["presence_ping_at"] = datetime.utcnow().isoformat()
        return None

    @app.after_request
    def add_api_cors_headers(response):
        if request.path.startswith("/api/"):
            allowed_origins = app.config.get("API_CORS_ALLOWED_ORIGINS", "*")
            response.headers.setdefault("Access-Control-Allow-Origin", allowed_origins)
            response.headers.setdefault("Access-Control-Allow-Headers", "Content-Type, Authorization, X-CSRFToken")
            response.headers.setdefault("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        return response


def register_error_handlers(app):
    from flask import jsonify, request
    from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

    def _is_json_api_request():
        return request.path.startswith("/api/") or (
            request.path.startswith("/search/") and request.is_json
        )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Die hochgeladene Datei ist zu gross."}), 413
        return error, 413

    @app.errorhandler(Exception)
    def handle_unexpected_api_error(error):
        if isinstance(error, HTTPException):
            return error
        if _is_json_api_request():
            app.logger.exception("API-Fehler:", exc_info=error)
            return jsonify({"success": False, "error": "Internal server error"}), 500
        raise error


def register_context_processors(app):
    from flask import session
    from flask_wtf.csrf import generate_csrf
    from app.models.user import User
    from app.extensions.main import db
    from app.services.billing import billing_enabled

    @app.context_processor
    def inject_csrf_token_and_user():
        user_id = session.get("user_id")
        current_user = None
        if user_id:
            current_user = db.session.get(User, user_id)
        return {
            "csrf_token": generate_csrf(),
            "g": {"current_user": current_user},
            "billing_enabled": billing_enabled(),
        }


def ensure_instance_directories(app):
    from pathlib import Path
    upload_directory = app.config.get("UPLOAD_DIRECTORY")
    if not upload_directory:
        upload_directory = Path(app.instance_path) / "uploads"
        app.config["UPLOAD_DIRECTORY"] = str(upload_directory)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_DIRECTORY"]).mkdir(parents=True, exist_ok=True)
