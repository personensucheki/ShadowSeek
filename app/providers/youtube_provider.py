import requests
from flask import current_app

from .base_provider import BaseProvider


class YouTubeProvider(BaseProvider):
    """
    YouTube Data API v3 Provider (offizielle API).

    Benötigt:
      - YOUTUBE_API_KEY

    Hinweis: Einnahmen sind nicht öffentlich. Wir liefern öffentlich verfügbare
    Kanalmetriken (Subscriber/View/Video-Count) sofern das Profil diese nicht versteckt.
    """

    def _api_key(self) -> str:
        key = current_app.config.get("YOUTUBE_API_KEY")
        if not key:
            raise ValueError("YouTube API nicht konfiguriert (YOUTUBE_API_KEY fehlt).")
        return key

    def _get(self, path: str, params: dict) -> dict:
        params = dict(params)
        params["key"] = self._api_key()
        resp = requests.get(f"https://www.googleapis.com/youtube/v3/{path.lstrip('/')}", params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()

    def _resolve_channel(self, handle_or_name: str) -> dict | None:
        query = handle_or_name.strip().lstrip("@")
        if not query:
            return None

        # 1) Prefer a direct handle query.
        handle_query = f"@{query}"
        search = self._get(
            "search",
            {
                "part": "snippet",
                "q": handle_query,
                "type": "channel",
                "maxResults": 1,
            },
        )
        items = search.get("items") or []
        if not items:
            # 2) Fallback: plain query.
            search = self._get(
                "search",
                {
                    "part": "snippet",
                    "q": query,
                    "type": "channel",
                    "maxResults": 1,
                },
            )
            items = search.get("items") or []
            if not items:
                return None

        channel_id = (items[0].get("id") or {}).get("channelId")
        if not channel_id:
            return None

        channels = self._get(
            "channels",
            {
                "part": "snippet,statistics",
                "id": channel_id,
                "maxResults": 1,
            },
        )
        ch_items = channels.get("items") or []
        if not ch_items:
            return None
        return ch_items[0]

    def search_creator(self, username, platform, realname=None, deepsearch=False):
        username = (username or "").strip()
        if not username:
            raise ValueError("username ist Pflicht.")

        profile_url = f"https://www.youtube.com/@{username.lstrip('@')}"

        try:
            channel = self._resolve_channel(username)
            if not channel:
                return {
                    "creator": {
                        "display_name": username.lstrip("@"),
                        "username": username.lstrip("@"),
                        "platform": "youtube",
                        "country": None,
                        "profile_url": profile_url,
                        "avatar": None,
                    },
                    "metrics": {
                        "subscribers": None,
                        "views_total": None,
                        "videos_total": None,
                        "estimated_earnings_today_usd": None,
                        "estimated_earnings_total_usd": None,
                        "diamonds_today": None,
                        "ranking_country": None,
                    },
                    "history": [],
                    "source": {
                        "provider": "youtube",
                        "type": "official_api",
                        "confidence": "low",
                        "last_updated": None,
                        "note": "Kein Kanal gefunden (oder API-Limit).",
                    },
                }

            snippet = channel.get("snippet") or {}
            stats = channel.get("statistics") or {}
            avatar = ((snippet.get("thumbnails") or {}).get("high") or {}).get("url")
            channel_title = snippet.get("title") or username.lstrip("@")

            # YouTube kann subscriberCount verstecken -> dann fehlt es.
            subscribers = stats.get("subscriberCount")
            views_total = stats.get("viewCount")
            videos_total = stats.get("videoCount")

            return {
                "creator": {
                    "display_name": channel_title,
                    "username": username.lstrip("@"),
                    "platform": "youtube",
                    "country": None,
                    "profile_url": profile_url,
                    "avatar": avatar,
                },
                "metrics": {
                    "subscribers": int(subscribers) if subscribers is not None else None,
                    "views_total": int(views_total) if views_total is not None else None,
                    "videos_total": int(videos_total) if videos_total is not None else None,
                    "estimated_earnings_today_usd": None,
                    "estimated_earnings_total_usd": None,
                    "diamonds_today": None,
                    "ranking_country": None,
                },
                "history": [],
                "source": {
                    "provider": "youtube",
                    "type": "official_api",
                    "confidence": "medium",
                    "last_updated": None,
                },
            }
        except requests.RequestException as exc:
            return {
                "creator": {
                    "display_name": username.lstrip("@"),
                    "username": username.lstrip("@"),
                    "platform": "youtube",
                    "country": None,
                    "profile_url": profile_url,
                    "avatar": None,
                },
                "metrics": {
                    "subscribers": None,
                    "views_total": None,
                    "videos_total": None,
                    "estimated_earnings_today_usd": None,
                    "estimated_earnings_total_usd": None,
                    "diamonds_today": None,
                    "ranking_country": None,
                },
                "history": [],
                "source": {
                    "provider": "youtube",
                    "type": "official_api",
                    "confidence": "low",
                    "last_updated": None,
                    "error": str(exc),
                },
            }

