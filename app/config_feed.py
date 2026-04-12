"""
Zentrale Konfiguration für Feed, Ranking und Recommendation
"""

FEED_CONFIG = {
    "RANKING_WEIGHTS": {
        "watch_time_seconds": 2.0,
        "completion_rate": 1.5,
        "rewatch_rate": 1.2,
        "shares": 1.0,
        "saves": 0.8,
        "comments_quality": 0.7,
        "profile_click_rate": 0.6,
        "follow_conversion": 0.6,
        "skip_rate": -1.0,
        "report_rate": -1.5,
        "freshness_bonus": 0.5,
        "creator_diversity_bonus": 0.3,
        "exploration_bonus": 0.2,
    },
    "LIVE_RANKING_WEIGHTS": {
        "viewer_growth_rate": 2.0,
        "avg_watch_time": 1.5,
        "chat_activity": 1.2,
        "retention_3min": 1.0,
        "creator_loyalty_score": 1.0,
        "quality_score": 0.8,
        "recency": 0.5,
    },
    "LOG_LEVEL": "INFO",
    "MAX_FEED_ITEMS": 50,
    "MAX_LIVE_ITEMS": 20,
}
