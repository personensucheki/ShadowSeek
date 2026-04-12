from .base_provider import BaseProvider


class TikTokProvider(BaseProvider):
    def search_creator(self, username, platform, realname=None, deepsearch=False):
        """
        Integrates the internal TikTok scraper module as the provider logic.
        """
        from app.modules.tiktok_scraper.app.runner import run_scraper
        import logging
        logger = logging.getLogger("tiktok_provider")
        logger.propagate = True
        logger.setLevel(logging.NOTSET)
        logger.info("TIKTOK_PROVIDER_TEST_EVENT_START: Provider entry method called.")
        logger.info(f"[TikTokProvider] Invoked for username='%s', platform='%s', realname='%s', deepsearch=%s", username, platform, realname, deepsearch)
        username = (username or "").strip().lstrip("@")
        logger.info("TIKTOK_PROVIDER_INPUT_ACCEPTED: Input normalized and accepted. username='%s'", username)
        if not username:
            logger.warning("[TikTokProvider] Invalid input: No username provided.")
            return {
                "creator": None,
                "metrics": None,
                "history": [],
                "source": {
                    "provider": "tiktok",
                    "type": "error",
                    "confidence": "low",
                    "last_updated": None,
                    "error": "No username provided"
                },
                "error": "No username provided"
            }
        url = f"https://www.tiktok.com/@{username}"
        logger.info("[TikTokProvider] Input normalized. Scraper will be called with url='%s'", url)
        try:
            result = run_scraper([url], options={"logger": logger})
        except Exception as e:
            logger.error("[TikTokProvider] Scraper invocation failed: %s", e)
            return {
                "creator": None,
                "metrics": None,
                "history": [],
                "source": {
                    "provider": "tiktok",
                    "type": "scraper_exception",
                    "confidence": "low",
                    "last_updated": None,
                    "error": str(e)
                },
                "error": str(e)
            }
        if not result["success"] or not result["data"]:
            logger.warning("[TikTokProvider] Scraper returned failure or empty result. Error: %s", result.get("error"))
            return {
                "creator": None,
                "metrics": None,
                "history": [],
                "source": {
                    "provider": "tiktok",
                    "type": "scraper_error",
                    "confidence": "low",
                    "last_updated": None,
                    "error": result.get("error")
                },
                "error": result.get("error")
            }
        data = result["data"][0]
        if data.get("status") != "success":
            logger.warning("[TikTokProvider] Scraper returned non-success status: %s, error_code=%s, error_message=%s", data.get("status"), data.get("error_code"), data.get("error_message"))
        else:
            logger.info("[TikTokProvider] Scraper succeeded for username='%s'. Outcome: status=%s, author=%s", username, data.get("status"), data.get("author_username"))
        return {
            "creator": {
                "display_name": data.get("author_username", "") or username.capitalize(),
                "username": data.get("author_username", "") or username,
                "platform": platform,
                "country": None,
                "profile_url": url,
                "avatar": None,
            },
            "metrics": {
                "views": data.get("views"),
                "likes": data.get("likes"),
                "comments_count": data.get("comments_count"),
                "shares": data.get("shares"),
            },
            "history": [],
            "source": {
                "provider": "tiktok",
                "type": "scraper",
                "confidence": data.get("status", "low"),
                "last_updated": data.get("scraped_at"),
                "error": data.get("error_message"),
            },
            "error": data.get("error_message")
        }

