import logging
import os

from .base_provider import BaseProvider


class TikTokProvider(BaseProvider):
    def search_creator(self, username, platform, realname=None, deepsearch=False):
        """
        Integrates the internal TikTok scraper module as provider logic.
        """
        from app.modules.tiktok_scraper.app.runner import run_scraper

        logger = logging.getLogger("tiktok_provider")
        logger.propagate = True
        logger.setLevel(logging.NOTSET)

        username = (username or "").strip().lstrip("@")
        logger.info(
            "[TikTokProvider] invoked: username=%s platform=%s realname=%s deepsearch=%s",
            username,
            platform,
            realname,
            deepsearch,
        )

        if not username:
            return {
                "creator": None,
                "metrics": None,
                "history": [],
                "source": {
                    "provider": "tiktok",
                    "type": "error",
                    "confidence": "low",
                    "last_updated": None,
                    "error": "No username provided",
                },
                "error": "No username provided",
            }

        url = f"https://www.tiktok.com/@{username}"
        timeout_ms = int(os.environ.get("TIKTOK_SCRAPER_TIMEOUT_MS", "12000"))

        try:
            result = run_scraper(
                [url],
                options={"logger": logger, "headless": True, "timeout_ms": timeout_ms},
            )
        except Exception as error:
            logger.error("[TikTokProvider] scraper invocation failed: %s", error)
            return {
                "creator": None,
                "metrics": None,
                "history": [],
                "source": {
                    "provider": "tiktok",
                    "type": "scraper_exception",
                    "confidence": "low",
                    "last_updated": None,
                    "error": str(error),
                },
                "error": str(error),
            }

        if not result.get("success") or not result.get("data"):
            logger.warning("[TikTokProvider] scraper returned failure/empty: %s", result.get("error"))
            return {
                "creator": None,
                "metrics": None,
                "history": [],
                "source": {
                    "provider": "tiktok",
                    "type": "scraper_error",
                    "confidence": "low",
                    "last_updated": None,
                    "error": result.get("error"),
                },
                "error": result.get("error"),
            }

        data = result["data"][0]
        author_username = data.get("author_username") or username

        if data.get("status") != "success":
            logger.warning(
                "[TikTokProvider] non-success status=%s code=%s msg=%s",
                data.get("status"),
                data.get("error_code"),
                data.get("error_message"),
            )

        return {
            "creator": {
                "display_name": data.get("author_nickname") or author_username,
                "username": author_username,
                "platform": platform,
                "country": None,
                "profile_url": f"https://www.tiktok.com/@{author_username}",
                "avatar": None,
            },
            "metrics": {
                "views": data.get("views"),
                "likes": data.get("likes") or data.get("likes_total"),
                "comments_count": data.get("comments_count"),
                "shares": data.get("shares"),
                "followers": data.get("followers"),
                "following": data.get("following"),
                "videos_total": data.get("videos_total"),
            },
            "history": [],
            "source": {
                "provider": "tiktok",
                "type": "scraper",
                "confidence": data.get("status", "low"),
                "last_updated": data.get("scraped_at") or data.get("scraped_profile_at"),
                "error": data.get("error_message"),
            },
            "error": None if data.get("status") == "success" else data.get("error_message"),
        }
