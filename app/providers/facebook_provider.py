from .base_provider import BaseProvider

class FacebookProvider(BaseProvider):
    def search_creator(self, username, platform, realname=None, deepsearch=False):
        # Dummy-Implementierung für Demo-Zwecke
        return {
            "creator": {
                "display_name": username.capitalize(),
                "username": username,
                "platform": platform,
                "country": None,
                "profile_url": f"https://facebook.com/{username}",
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
                "provider": "facebook",
                "type": "estimated_public_data",
                "confidence": "low",
                "last_updated": None
            }
        }
