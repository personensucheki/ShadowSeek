import os


def _normalize_database_uri(uri):
    if uri.startswith("postgres://"):
        return uri.replace("postgres://", "postgresql://", 1)
    return uri


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
    UPLOAD_DIRECTORY = os.environ.get("UPLOAD_DIRECTORY")
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
    STRIPE_PRICE_ID_ABO_3 = os.environ.get("STRIPE_PRICE_ID_ABO_3", "")
    STRIPE_PRICE_ID_ABO_4 = os.environ.get("STRIPE_PRICE_ID_ABO_4", "")




class DevConfig(BaseConfig):
    DEBUG = True
    SECRET_KEY = BaseConfig.SECRET_KEY or "shadowseek-dev-secret"
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False




class ProdConfig(BaseConfig):
    DEBUG = False
