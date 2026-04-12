import requests
from flask import current_app

from .base_provider import BaseProvider


class RedditProvider(BaseProvider):
    """
    Reddit Public JSON Provider.

    Nutzt:
      - https://www.reddit.com/user/<name>/about.json

    Reddit kann rate-limiten; wir liefern dann fallback + Link.
    """

    def search_creator(self, username, platform, realname=None, deepsearch=False):
        username = (username or "").strip().lstrip("u/").lstrip("@")
        if not username:
            raise ValueError("username ist Pflicht.")

        profile_url = f"https://www.reddit.com/user/{username}/"
        headers = {
            "User-Agent": current_app.config.get("REDDIT_USER_AGENT") or "ShadowSeek/1.0",
            "Accept": "application/json",
        }

        try:
            resp = requests.get(
                f"https://www.reddit.com/user/{username}/about.json",
                headers=headers,
                timeout=8,
            )
            if resp.status_code == 404:
                return {
                    "creator": {
                        "display_name": username,
                        "username": username,
                        "platform": "reddit",
                        "country": None,
                        "profile_url": profile_url,
                        "avatar": None,
                    },
                    "metrics": {
                        "karma_total": None,
                        "created_utc": None,
                        "estimated_earnings_today_usd": None,
                        "estimated_earnings_total_usd": None,
                        "diamonds_today": None,
                        "ranking_country": None,
                    },
                    "history": [],
                    "source": {
                        "provider": "reddit",
                        "type": "public_json",
                        "confidence": "low",
                        "last_updated": None,
                        "note": "Reddit-User nicht gefunden.",
                    },
                }

            resp.raise_for_status()
            payload = resp.json()
            data = payload.get("data") or {}
            icon = data.get("icon_img") or data.get("snoovatar_img") or None
            karma_total = None
            if data.get("total_karma") is not None:
                karma_total = int(data.get("total_karma"))
            elif data.get("link_karma") is not None or data.get("comment_karma") is not None:
                karma_total = int(data.get("link_karma") or 0) + int(data.get("comment_karma") or 0)

            return {
                "creator": {
                    "display_name": data.get("name") or username,
                    "username": data.get("name") or username,
                    "platform": "reddit",
                    "country": None,
                    "profile_url": profile_url,
                    "avatar": icon if icon else None,
                },
                "metrics": {
                    "karma_total": karma_total,
                    "created_utc": data.get("created_utc"),
                    "estimated_earnings_today_usd": None,
                    "estimated_earnings_total_usd": None,
                    "diamonds_today": None,
                    "ranking_country": None,
                },
                "history": [],
                "source": {
                    "provider": "reddit",
                    "type": "public_json",
                    "confidence": "medium",
                    "last_updated": None,
                },
            }
        except requests.RequestException as exc:
            return {
                "creator": {
                    "display_name": username,
                    "username": username,
                    "platform": "reddit",
                    "country": None,
                    "profile_url": profile_url,
                    "avatar": None,
                },
                "metrics": {
                    "karma_total": None,
                    "created_utc": None,
                    "estimated_earnings_today_usd": None,
                    "estimated_earnings_total_usd": None,
                    "diamonds_today": None,
                    "ranking_country": None,
                },
                "history": [],
                "source": {
                    "provider": "reddit",
                    "type": "public_json",
                    "confidence": "low",
                    "last_updated": None,
                    "error": str(exc),
                },
            }

