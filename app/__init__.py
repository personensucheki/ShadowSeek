import os
from dotenv import load_dotenv
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
    # .env laden, bevor Config/ENV-Validation ausgewertet wird
    load_dotenv()
    import sys

    selected_config = config_class or _resolve_default_config()
    is_testing_mode = bool(getattr(selected_config, "TESTING", False)) or bool(
        os.environ.get("PYTEST_CURRENT_TEST")
    )
    is_production_runtime = bool(os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"))

    # --- ENV VALIDATION LAYER ---
    required_env = [
        "SECRET_KEY",
        "DATABASE_URL",
        "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRICE_ID_ABO_1",
        "STRIPE_PRICE_ID_ABO_2",
        "STRIPE_PRICE_ID_ABO_3",
        "STRIPE_PRICE_ID_ABO_4",
    ]
    optional_env = [
        "OPENAI_API_KEY",
        "SERPER_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "TWITCH_CLIENT_ID",
        "TWITCH_CLIENT_SECRET",
        "YOUTUBE_API_KEY",
        "REDDIT_USER_AGENT",
    ]
    missing_required = [k for k in required_env if not os.environ.get(k)]
    missing_optional = [k for k in optional_env if not os.environ.get(k)]
    disabled_features = []
    if not os.environ.get("OPENAI_API_KEY"):
        disabled_features.append("AI rerank (OpenAI)")
    if not os.environ.get("SERPER_API_KEY"):
        disabled_features.append("Websearch (Serper)")
    if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
        disabled_features.append("Telegram alerts")
    if not os.environ.get("TWITCH_CLIENT_ID") or not os.environ.get("TWITCH_CLIENT_SECRET"):
        disabled_features.append("Twitch integration")
    if not os.environ.get("YOUTUBE_API_KEY"):
        disabled_features.append("YouTube integration")
    if not os.environ.get("REDDIT_USER_AGENT"):
        disabled_features.append("Reddit integration")

    # Strict validation only in production runtime and not for tests.
    if missing_required and is_production_runtime and not is_testing_mode:
        print("\n[ENV VALIDATION] FATAL: Missing required environment variables:", file=sys.stderr)
        for k in missing_required:
            print(f"  - {k}", file=sys.stderr)
        print("\n[ENV VALIDATION] Application startup aborted due to missing critical configuration.\n", file=sys.stderr)
        raise RuntimeError("Missing required production environment variables.")
    elif missing_required:
        print(
            "\n[ENV VALIDATION] WARNING: Missing required env for production, "
            "but strict fail is skipped outside production runtime.",
            file=sys.stderr,
        )
        for k in missing_required:
            print(f"  - {k}", file=sys.stderr)

    if missing_optional:
        print("\n[ENV VALIDATION] WARNING: Missing optional environment variables:", file=sys.stderr)
        for k in missing_optional:
            print(f"  - {k}", file=sys.stderr)

    if disabled_features:
        print("\n[ENV VALIDATION] Optional features disabled due to missing ENV:", file=sys.stderr)
        for feat in disabled_features:
            print(f"  - {feat}", file=sys.stderr)

    import logging
    from logging.handlers import RotatingFileHandler
    from app.services.response_utils import api_error

    # --- LOGGING SETUP ---
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "app.log")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Remove default handlers to avoid duplicate logs
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)
    file_handler = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=5, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    # Console handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    logging.info("Logging initialized. Log file: %s", log_file)

    app = Flask(__name__, instance_relative_config=True)

    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.exception("Global unhandled exception: %s", e)
        return api_error(
            message="Internal server error",
            status=500,
            errors={"type": "internal_error"}
        )

    app.config.from_object(selected_config)

    _configure_database_uri(app)
    app.config["PLANS"] = build_configured_plans(app.config)

    upload_directory = app.config.get("UPLOAD_DIRECTORY")
    if not upload_directory:
        upload_directory = Path(app.instance_path) / "uploads"
        app.config["UPLOAD_DIRECTORY"] = str(upload_directory)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_DIRECTORY"]).mkdir(parents=True, exist_ok=True)

    if not app.config.get("SECRET_KEY") and not app.config.get("TESTING"):
        print("[ENV VALIDATION] FATAL: SECRET_KEY must be configured for ShadowSeek.", file=sys.stderr)
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
