from __future__ import annotations

from flask import Blueprint, jsonify

import logging
from flask import current_app
from app.services.google_live_provider_service import google_live_provider_service
from app.services.provider_errors import ProviderError
from app.services.response_utils import api_success, api_error

provider_status_bp = Blueprint("provider_status", __name__, url_prefix="/api/providers")

def safe_provider_status(name, fn):
    try:
        status = fn()
        # Wenn Provider-Objekt provider_status liefert, direkt übernehmen
        if isinstance(status, dict) and "provider_status" in status:
            return status
        return {"provider_status": "ok", "detail": status}
    except ProviderError as exc:
        return {
            "provider_status": "disabled",
            "error_type": type(exc).__name__,
            "error_msg": exc.message,
            "detail": exc.as_dict(),
        }
    except ValueError as exc:
        message = str(exc)
        if "nicht konfiguriert" in message or "fehlt" in message:
            return {
                "provider_status": "disabled",
                "error_type": type(exc).__name__,
                "error_msg": message,
            }
        logging.exception("Provider %s error: %s", name, exc)
        return {"provider_status": "error", "error_type": type(exc).__name__, "error_msg": message}
    except Exception as exc:
        logging.exception("Provider %s error: %s", name, exc)
        return {"provider_status": "error", "error_type": type(exc).__name__, "error_msg": str(exc)}

@provider_status_bp.get("/status")
def provider_status():
    providers = {}
    # Google Provider
    providers["google"] = safe_provider_status("google", google_live_provider_service.status)
    # TikTok Provider (optional)
    try:
        from app.providers.tiktok_public_provider import TikTokPublicRevenueProvider
        providers["tiktok"] = safe_provider_status("tiktok", lambda: TikTokPublicRevenueProvider().fetch())
    except Exception as exc:
        logging.exception("Provider tiktok import error: %s", exc)
        providers["tiktok"] = {"provider_status": "disabled", "error_type": type(exc).__name__, "error_msg": str(exc)}
    # Reddit Provider (optional)
    try:
        from app.providers.reddit_provider import RedditProvider
        providers["reddit"] = safe_provider_status("reddit", lambda: RedditProvider().search_creator("shadowseek", "reddit"))
    except Exception as exc:
        logging.exception("Provider reddit import error: %s", exc)
        providers["reddit"] = {"provider_status": "disabled", "error_type": type(exc).__name__, "error_msg": str(exc)}
    # YouTube Provider (optional)
    try:
        from app.providers.youtube_provider import YouTubeProvider
        providers["youtube"] = safe_provider_status("youtube", lambda: YouTubeProvider()._api_key())
    except Exception as exc:
        logging.exception("Provider youtube import error: %s", exc)
        providers["youtube"] = {"provider_status": "disabled", "error_type": type(exc).__name__, "error_msg": str(exc)}
    # Twitch Provider (optional)
    try:
        from app.providers.twitch_provider import TwitchProvider
        providers["twitch"] = safe_provider_status("twitch", lambda: TwitchProvider()._get_app_token())
    except Exception as exc:
        logging.exception("Provider twitch import error: %s", exc)
        providers["twitch"] = {"provider_status": "disabled", "error_type": type(exc).__name__, "error_msg": str(exc)}
    # Demo Provider (optional)
    try:
        from app.providers.demo_revenue_provider import DemoRevenueProvider
        providers["demo"] = safe_provider_status("demo", lambda: DemoRevenueProvider().fetch())
    except Exception as exc:
        logging.exception("Provider demo import error: %s", exc)
        providers["demo"] = {"provider_status": "disabled", "error_type": type(exc).__name__, "error_msg": str(exc)}

    return api_success(data=providers)
