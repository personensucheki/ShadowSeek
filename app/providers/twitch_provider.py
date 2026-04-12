import time
from dataclasses import dataclass

import requests
from flask import current_app

from .base_provider import BaseProvider


@dataclass
class _TwitchToken:
    access_token: str
    expires_at: float


class TwitchProvider(BaseProvider):
    """
    Twitch Helix Provider (offizielle API).

    Benötigt:
      - TWITCH_CLIENT_ID
      - TWITCH_CLIENT_SECRET

    Hinweis: Twitch stellt keine "Live-Einnahmen" öffentlich bereit. Wir liefern
    öffentlich/über App-Token verfügbare Metriken (z.B. Follower, Views) und Links.
    """

    _token: _TwitchToken | None = None

    def _get_app_token(self) -> str:
        client_id = current_app.config.get("TWITCH_CLIENT_ID")
        client_secret = current_app.config.get("TWITCH_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise ValueError("Twitch API nicht konfiguriert (TWITCH_CLIENT_ID/TWITCH_CLIENT_SECRET fehlen).")

        now = time.time()
        if self._token and self._token.expires_at - 30 > now:
            return self._token.access_token

        resp = requests.post(
            "https://id.twitch.tv/oauth2/token",
            data={"client_id": client_id, "client_secret": client_secret, "grant_type": "client_credentials"},
            timeout=8,
        )
        resp.raise_for_status()
        payload = resp.json()
        access_token = payload.get("access_token")
        expires_in = int(payload.get("expires_in") or 0)
        if not access_token or expires_in <= 0:
            raise ValueError("Twitch OAuth Token konnte nicht erstellt werden.")

        self._token = _TwitchToken(access_token=access_token, expires_at=now + expires_in)
        return access_token

    def _helix_get(self, path: str, params: dict) -> dict:
        client_id = current_app.config.get("TWITCH_CLIENT_ID")
        token = self._get_app_token()
        headers = {"Client-Id": client_id, "Authorization": f"Bearer {token}"}
        resp = requests.get(f"https://api.twitch.tv/helix/{path.lstrip('/')}", headers=headers, params=params, timeout=8)
        resp.raise_for_status()
        return resp.json()

    def search_creator(self, username, platform, realname=None, deepsearch=False):
        username = (username or "").strip().lstrip("@")
        if not username:
            raise ValueError("username ist Pflicht.")

        profile_url = f"https://www.twitch.tv/{username}"

        try:
            user_res = self._helix_get("users", {"login": username})
            items = user_res.get("data") or []
            if not items:
                return {
                    "creator": {
                        "display_name": username,
                        "username": username,
                        "platform": "twitch",
                        "country": None,
                        "profile_url": profile_url,
                        "avatar": None,
                    },
                    "metrics": {
                        "followers": None,
                        "views_total": None,
                        "estimated_earnings_today_usd": None,
                        "estimated_earnings_total_usd": None,
                        "diamonds_today": None,
                        "ranking_country": None,
                    },
                    "history": [],
                    "source": {
                        "provider": "twitch",
                        "type": "official_api",
                        "confidence": "medium",
                        "last_updated": None,
                        "note": "Kein Twitch-User gefunden.",
                    },
                }

            user = items[0]
            user_id = user.get("id")

            followers = None
            if user_id:
                # Helix "Get Users Follows" wurde deprec. in Teilen; trotzdem ist
                # in vielen Accounts weiterhin verfügbar. Falls Twitch 410/400
                # liefert, lassen wir followers = None.
                try:
                    follow_res = self._helix_get("channels/followers", {"broadcaster_id": user_id, "first": 1})
                    followers = follow_res.get("total")
                except requests.RequestException:
                    followers = None

            return {
                "creator": {
                    "display_name": user.get("display_name") or username,
                    "username": user.get("login") or username,
                    "platform": "twitch",
                    "country": None,
                    "profile_url": profile_url,
                    "avatar": user.get("profile_image_url"),
                },
                "metrics": {
                    "followers": followers,
                    "views_total": user.get("view_count"),
                    "estimated_earnings_today_usd": None,
                    "estimated_earnings_total_usd": None,
                    "diamonds_today": None,
                    "ranking_country": None,
                },
                "history": [],
                "source": {
                    "provider": "twitch",
                    "type": "official_api",
                    "confidence": "medium",
                    "last_updated": None,
                },
            }
        except requests.RequestException as exc:
            return {
                "creator": {
                    "display_name": username,
                    "username": username,
                    "platform": "twitch",
                    "country": None,
                    "profile_url": profile_url,
                    "avatar": None,
                },
                "metrics": {
                    "followers": None,
                    "views_total": None,
                    "estimated_earnings_today_usd": None,
                    "estimated_earnings_total_usd": None,
                    "diamonds_today": None,
                    "ranking_country": None,
                },
                "history": [],
                "source": {
                    "provider": "twitch",
                    "type": "official_api",
                    "confidence": "low",
                    "last_updated": None,
                    "error": str(exc),
                },
            }

