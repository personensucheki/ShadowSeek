import os

from app.providers.demo_revenue_provider import DemoRevenueProvider
from app.providers.tiktok_public_provider import TikTokPublicRevenueProvider
from app.providers.facebook_provider import FacebookProvider
from app.providers.instagram_provider import InstagramProvider
from app.providers.twitch_provider import TwitchProvider
from app.providers.knuddels_provider import KnuddelsProvider
from app.providers.lavoo_provider import LavooProvider
from app.providers.tinder_provider import TinderProvider
from app.providers.badoo_provider import BadooProvider
from app.providers.stripchat_provider import StripchatProvider
from app.providers.xhamster_provider import XHamsterProvider
from app.providers.mydirtyhobby_provider import MyDirtyHobbyProvider
from app.providers.pornhub_provider import PornhubProvider

def get_revenue_providers():
    providers = []
    if os.getenv("ENABLE_DEMO_PROVIDER", "true").lower() == "true":
        providers.append(DemoRevenueProvider())
    if os.getenv("ENABLE_TIKTOK_PROVIDER", "false").lower() == "true":
        providers.append(TikTokPublicRevenueProvider())
    if os.getenv("ENABLE_FACEBOOK_PROVIDER", "false").lower() == "true":
        providers.append(FacebookProvider())
    if os.getenv("ENABLE_INSTAGRAM_PROVIDER", "false").lower() == "true":
        providers.append(InstagramProvider())
    if os.getenv("ENABLE_TWITCH_PROVIDER", "false").lower() == "true":
        providers.append(TwitchProvider())
    if os.getenv("ENABLE_KNUDDELS_PROVIDER", "false").lower() == "true":
        providers.append(KnuddelsProvider())
    if os.getenv("ENABLE_LAVOO_PROVIDER", "false").lower() == "true":
        providers.append(LavooProvider())
    if os.getenv("ENABLE_TINDER_PROVIDER", "false").lower() == "true":
        providers.append(TinderProvider())
    if os.getenv("ENABLE_BADOO_PROVIDER", "false").lower() == "true":
        providers.append(BadooProvider())
    if os.getenv("ENABLE_STRIPCHAT_PROVIDER", "false").lower() == "true":
        providers.append(StripchatProvider())
    if os.getenv("ENABLE_XHAMSTER_PROVIDER", "false").lower() == "true":
        providers.append(XHamsterProvider())
    if os.getenv("ENABLE_MYDIRTYHOBBY_PROVIDER", "false").lower() == "true":
        providers.append(MyDirtyHobbyProvider())
    if os.getenv("ENABLE_PORNHUB_PROVIDER", "false").lower() == "true":
        providers.append(PornhubProvider())
    return providers
