import random
from datetime import datetime, timedelta
import logging
import os
from app import create_app
from app.extensions import db
from app.models.revenue import RevenueEvent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CREATORS = [
    {"platform": "tiktok", "username": "demo_tiktok_1", "display_name": "TikTok Star 1"},
    {"platform": "tiktok", "username": "demo_tiktok_2", "display_name": "TikTok Star 2"},
    {"platform": "twitch", "username": "demo_twitch_1", "display_name": "Twitch Hero 1"},
    {"platform": "twitch", "username": "demo_twitch_2", "display_name": "Twitch Hero 2"},
    {"platform": "youtube", "username": "demo_youtube_1", "display_name": "YouTube Ace 1"},
    {"platform": "youtube", "username": "demo_youtube_2", "display_name": "YouTube Ace 2"},
    {"platform": "tiktok", "username": "demo_tiktok_3", "display_name": "TikTok Star 3"},
    {"platform": "twitch", "username": "demo_twitch_3", "display_name": "Twitch Hero 3"},
]

DAYS = 14


def seed_history():
    app = create_app()
    with app.app_context():
        for creator in CREATORS:
            base = 100 + hash(creator["username"]) % 200
            for day in range(DAYS):
                date = datetime.utcnow() - timedelta(days=day)
                estimated_revenue = round(base + random.uniform(-20, 40) + day * random.uniform(-2, 2), 2)
                diamonds = int(estimated_revenue * 200)
                followers = 100000 + (hash(creator["username"]) % 50000)
                event = RevenueEvent(
                    platform=creator["platform"],
                    username=creator["username"],
                    display_name=creator["display_name"],
                    estimated_revenue=estimated_revenue,
                    currency=os.getenv("REVENUE_DEFAULT_CURRENCY", "EUR"),
                    diamonds=diamonds,
                    followers=followers,
                    source="seed_history",
                    confidence="low",
                    captured_at=date,
                )
                db.session.add(event)
        db.session.commit()
        logger.info(f"Seeded {len(CREATORS) * DAYS} revenue events.")

if __name__ == "__main__":
    seed_history()
