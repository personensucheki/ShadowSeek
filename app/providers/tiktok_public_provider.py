import logging
from typing import List, Dict, Any
from .base_revenue_provider import BaseRevenueProvider

logger = logging.getLogger(__name__)

class TikTokPublicRevenueProvider(BaseRevenueProvider):
    name = "tiktok_public"

    def fetch(self) -> List[Dict[str, Any]]:
        try:
            # TODO: Implement real fetching logic
            # For now, return empty list as stub
            return []
        except Exception as exc:
            logger.exception("TikTokPublicRevenueProvider error: %s", exc)
            return []
