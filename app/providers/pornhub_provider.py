from .base_provider import BaseProvider

class PornhubProvider(BaseProvider):
    def search_creator(self, username, platform, realname=None, deepsearch=False):
        # Dummy-Implementierung für Demo-Zwecke
        return {
            "creator": {
                "display_name": username.capitalize(),
                "username": username,
                "platform": platform,
                "country": None,
                "profile_url": f"https://pornhub.com/model/{username}",
                "avatar": None
            },
            "metrics": {
                "followers": None,
                "posts": None,
                "engagement": None,
                "ranking_country": None
            },
            "history": [],
            "source": {
                "provider": "pornhub",
                "type": "estimated_public_data",
                "confidence": "low",
                "last_updated": None
            }
        }
