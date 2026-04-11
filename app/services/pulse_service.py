from app.providers.tiktok_provider import TikTokProvider

PLATFORM_PROVIDERS = {
    "tiktok": TikTokProvider(),
    # Weitere Plattformen später ergänzen
}

def search_creator_service(username, platform, realname=None, deepsearch=False):
    platform = platform.lower()
    provider = PLATFORM_PROVIDERS.get(platform)
    if not provider:
        raise ValueError(f"Platform '{platform}' not supported.")
    return provider.search_creator(username, platform, realname, deepsearch)
