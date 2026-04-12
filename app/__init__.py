import os
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, jsonify, request, session
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import RequestEntityTooLarge

from .extensions.main import csrf, db, migrate
from .extensions.socketio import socketio, init_socketio
from .services.billing import build_configured_plans
from .services.owner_bootstrap import ensure_owner_account

from app.sockets.live_socket import init_app as register_live_socket_handlers


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
    """
    Select config class based on environment variables.
    Defaults to DevelopmentConfig, uses ProductionConfig for prod/Render.
    """
    from .config import DevelopmentConfig, ProductionConfig, TestingConfig

    # Render should always force production defaults, even if FLASK_ENV is still "development".
    if os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
        return ProductionConfig

    environment = (
        os.environ.get("SHADOWSEEK_ENV")
        or os.environ.get("FLASK_ENV")
        or os.environ.get("APP_ENV")
        or ""
    ).strip().lower()

    if environment in {"test", "testing"}:
        return TestingConfig
    if environment in {"prod", "production"}:
        return ProductionConfig
    return DevelopmentConfig


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
    init_socketio(app)
    app.socketio = socketio
    from .helpers.factory import (
        ensure_instance_directories,
        register_blueprints,
        register_context_processors,
        register_error_handlers,
        register_hooks,
    )

    ensure_instance_directories(app)
    register_context_processors(app)
    register_error_handlers(app)
    register_hooks(app)
    register_blueprints(app)
    register_live_socket_handlers(app)

    # Optional: create/update a first owner account from env vars.
    with app.app_context():
        ensure_owner_account(app)

    @app.get("/healthz")
    def healthz():
        return {"ok": True, "app": "ShadowSeek"}
    return app
