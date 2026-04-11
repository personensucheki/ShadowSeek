from .base_provider import BaseProvider

class TikTokProvider(BaseProvider):
    def search_creator(self, username, platform, realname=None, deepsearch=False):
        # Dummy-Implementierung für Demo-Zwecke
        return {
            "creator": {
                "display_name": username.capitalize(),
                "username": username,
                "platform": platform,
                "country": "Germany",
                "profile_url": None,
                "avatar": None
            },
            "metrics": {
                "estimated_earnings_today_usd": 0,
                "estimated_earnings_total_usd": 0,
                "diamonds_today": 0,
                "followers": None,
                "ranking_country": None
            },
            "history": [],
            "source": {
                "provider": "tiktok",
                "type": "estimated_public_data",
                "confidence": "low",
                "last_updated": None
            }
        }
