import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .base_revenue_provider import BaseRevenueProvider

class DemoRevenueProvider(BaseRevenueProvider):
    name = "demo_provider"

    def __init__(self, num_creators: int = 8):
        self.num_creators = num_creators
        self.creator_profiles = [
            {
                "platform": "tiktok",
                "username": f"demo_creator_{i+1}",
                "display_name": f"Demo Creator {i+1}",
                "currency": "EUR",
                "source": self.name,
                "confidence": "low"
            }
            for i in range(self.num_creators)
        ]

    def fetch(self) -> List[Dict[str, Any]]:
        now = datetime.utcnow()
        results = []
        for profile in self.creator_profiles:
            base_revenue = 100 + profile["username"].__hash__() % 100
            estimated_revenue = round(base_revenue + random.uniform(-10, 30), 2)
            diamonds = int(estimated_revenue * 200)
            followers = 100000 + (profile["username"].__hash__() % 50000)
            row = {
                **profile,
                "estimated_revenue": estimated_revenue,
                "diamonds": diamonds,
                "followers": followers,
                "captured_at": now.isoformat(),
            }
            results.append(row)
        return results
