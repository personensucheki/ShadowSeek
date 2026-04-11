import os
from app.providers.demo_revenue_provider import DemoRevenueProvider
from app.providers.tiktok_public_provider import TikTokPublicRevenueProvider

def get_revenue_providers():
    providers = []
    if os.getenv("ENABLE_DEMO_PROVIDER", "true").lower() == "true":
        providers.append(DemoRevenueProvider())
    if os.getenv("ENABLE_TIKTOK_PROVIDER", "false").lower() == "true":
        providers.append(TikTokPublicRevenueProvider())
    return providers
