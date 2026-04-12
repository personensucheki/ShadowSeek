from app.providers.reddit_provider import RedditProvider
from app.providers.tiktok_provider import TikTokProvider
from app.providers.twitch_provider import TwitchProvider
from app.providers.youtube_provider import YouTubeProvider


PLATFORM_PROVIDERS = {
    "tiktok": TikTokProvider(),
    "twitch": TwitchProvider(),
    "youtube": YouTubeProvider(),
    "reddit": RedditProvider(),
}


def search_creator_service(username, platform, realname=None, deepsearch=False):
    platform = (platform or "").strip().lower()
    provider = PLATFORM_PROVIDERS.get(platform)
    if not provider:
        # Kein Scraping/ToS-Umgehung: nur offizielle/public Quellen.
        raise ValueError(
            f"Platform '{platform}' not supported (no official/public metrics source configured)."
        )
    return provider.search_creator(username, platform, realname, deepsearch)

