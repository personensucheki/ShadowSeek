import os


def _normalize_database_uri(uri):
    if not uri:
        return uri

    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

    if uri.startswith("postgresql://") and not uri.startswith("postgresql+"):
        return uri.replace("postgresql://", "postgresql+psycopg://", 1)

    return uri


def _default_upload_directory():
    configured = os.environ.get("UPLOAD_DIRECTORY")
    if configured:
        return configured

    # Render persistent disks are commonly mounted at /data.
    if os.environ.get("RENDER") or os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
        return "/data/uploads"

    return None


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = _normalize_database_uri(
        os.environ.get("DATABASE_URL", "sqlite:///shadowseek.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 3600
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))
    SEARCH_REQUEST_TIMEOUT = float(os.environ.get("SEARCH_REQUEST_TIMEOUT", 3.5))
    SEARCH_MAX_WORKERS = int(os.environ.get("SEARCH_MAX_WORKERS", 8))
    REVERSE_IMAGE_MAX_AGE = int(os.environ.get("REVERSE_IMAGE_MAX_AGE", 3600))
    PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    UPLOAD_DIRECTORY = _default_upload_directory()
    SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
    SERPER_API_URL = os.environ.get("SERPER_API_URL", "https://google.serper.dev/search")
    SERPER_RESULTS_PER_QUERY = int(os.environ.get("SERPER_RESULTS_PER_QUERY", 8))
    SERPER_GL = os.environ.get("SERPER_GL", "de")
    SERPER_HL = os.environ.get("SERPER_HL", "de")
    PUBLIC_SEARCH_FALLBACK_ENABLED = os.environ.get(
        "PUBLIC_SEARCH_FALLBACK_ENABLED",
        "true",
    ).strip().lower() in {"1", "true", "yes", "on"}
    BING_SEARCH_URL = os.environ.get("BING_SEARCH_URL", "https://www.bing.com/search")
    BING_RESULTS_PER_QUERY = int(os.environ.get("BING_RESULTS_PER_QUERY", 8))
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_RERANK_MODEL = os.environ.get("OPENAI_RERANK_MODEL", "gpt-5-mini")
    OPENAI_TIMEOUT = float(os.environ.get("OPENAI_TIMEOUT", 12))
    OPENAI_MAX_RERANK_CANDIDATES = int(os.environ.get("OPENAI_MAX_RERANK_CANDIDATES", 12))
    TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID")
    TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET")
    YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "ShadowSeek/1.0 (contact: admin@shadowseek.local)")
    APP_BASE_URL = os.environ.get("APP_BASE_URL", PUBLIC_BASE_URL or "http://localhost:5000").rstrip("/")
    BILLING_GATING_ENABLED = os.environ.get("BILLING_GATING_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
    STRIPE_API_VERSION = os.environ.get("STRIPE_API_VERSION", "2025-03-31.basil")
    STRIPE_PRICE_ID_ABO_1 = os.environ.get("STRIPE_PRICE_ID_ABO_1", "")
    STRIPE_PRICE_ID_ABO_2 = os.environ.get("STRIPE_PRICE_ID_ABO_2", "")
    # --- Multi-Plattform API Keys/Token ---
    FACEBOOK_API_KEY = os.environ.get("FACEBOOK_API_KEY")
    FACEBOOK_API_SECRET = os.environ.get("FACEBOOK_API_SECRET")
    INSTAGRAM_API_KEY = os.environ.get("INSTAGRAM_API_KEY")
    INSTAGRAM_API_SECRET = os.environ.get("INSTAGRAM_API_SECRET")
    KNUDDELS_API_KEY = os.environ.get("KNUDDELS_API_KEY")
    LAVOO_API_KEY = os.environ.get("LAVOO_API_KEY")
    TINDER_API_KEY = os.environ.get("TINDER_API_KEY")
    BADOO_API_KEY = os.environ.get("BADOO_API_KEY")
    STRIPCHAT_API_KEY = os.environ.get("STRIPCHAT_API_KEY")
    XHAMSTER_API_KEY = os.environ.get("XHAMSTER_API_KEY")
    MYDIRTYHOBBY_API_KEY = os.environ.get("MYDIRTYHOBBY_API_KEY")
    PORNHUB_API_KEY = os.environ.get("PORNHUB_API_KEY")
    STRIPE_PRICE_ID_ABO_3 = os.environ.get("STRIPE_PRICE_ID_ABO_3", "")
    STRIPE_PRICE_ID_ABO_4 = os.environ.get("STRIPE_PRICE_ID_ABO_4", "")
    OWNER_BOOTSTRAP_ENABLED = os.environ.get("OWNER_BOOTSTRAP_ENABLED", "false")
    OWNER_BOOTSTRAP_USERNAME = os.environ.get("OWNER_BOOTSTRAP_USERNAME", "")
    OWNER_BOOTSTRAP_EMAIL = os.environ.get("OWNER_BOOTSTRAP_EMAIL", "")
    OWNER_BOOTSTRAP_PASSWORD = os.environ.get("OWNER_BOOTSTRAP_PASSWORD", "")




class DevConfig(BaseConfig):
    DEBUG = True
    SECRET_KEY = BaseConfig.SECRET_KEY or "shadowseek-dev-secret"
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False




class ProdConfig(BaseConfig):
    DEBUG = False
