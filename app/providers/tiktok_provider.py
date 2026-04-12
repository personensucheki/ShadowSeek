from .base_provider import BaseProvider


class TikTokProvider(BaseProvider):
    def search_creator(self, username, platform, realname=None, deepsearch=False):
        # Hinweis: TikTok stellt keine verifizierbaren Revenue-/Analytics-Daten
        # ohne offiziellen Partnerzugang/OAuth bereit. Wir liefern bewusst nur
        # eine klare Fallback-Antwort (keine Fake-Zahlen).
        username = (username or "").strip().lstrip("@")
        return {
            "creator": {
                "display_name": username.capitalize() if username else "",
                "username": username,
                "platform": platform,
                "country": None,
                "profile_url": f"https://www.tiktok.com/@{username}" if username else None,
                "avatar": None,
            },
            "metrics": {
                "estimated_earnings_today_usd": None,
                "estimated_earnings_total_usd": None,
                "diamonds_today": None,
                "followers": None,
                "ranking_country": None,
            },
            "history": [],
            "source": {
                "provider": "tiktok",
                "type": "not_available",
                "confidence": "low",
                "last_updated": None,
                "note": "Keine offiziellen/public Analytics verfuegbar ohne Partnerzugang/OAuth.",
            },
        }

