"""
Live-Service: Verwaltung und Scoring von Livestream-Kandidaten.

Wichtig:
- Dieses Modul liefert bewusst nur lokale Heuristiken und keine externen Plattform-Scrapes.
- Es ist so gebaut, dass es **nicht** den App-Start bricht, auch wenn Live-Feeds noch nicht final sind.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config_feed import FEED_CONFIG


@dataclass(frozen=True)
class LiveScoreResult:
    score: float
    breakdown: dict[str, float]


class LiveService:
    def score_live_candidate(
        self,
        session: Any,
        user_profile: dict[str, Any] | None,
        session_state: dict[str, Any] | None = None,
        *,
        return_breakdown: bool = False,
    ):
        """
        Bewertet eine Live-Session nach gewichteter, lokaler Formel.
        Erwartet `session` als dict oder Objekt mit Attributes.
        """
        user_profile = user_profile or {}
        weights = FEED_CONFIG.get(
            "LIVE_SCORE_WEIGHTS",
            {
                "viewer_growth_rate": 0.20,
                "avg_watchtime": 0.18,
                "retention_3min": 0.14,
                "chat_velocity": 0.12,
                "gift_signal": 0.08,
                "follow_from_live_rate": 0.07,
                "creator_loyalty": 0.06,
                "topic_match": 0.05,
                "locality_match": 0.04,
                "stream_quality_score": 0.06,
                "recency": 0.05,
                "early_exit_rate": -0.16,
                "report_rate": -0.18,
                "risk_penalty": -0.10,
            },
        )

        def read_feature(key: str, default: float = 0.0) -> float:
            if hasattr(session, key):
                try:
                    return float(getattr(session, key))
                except Exception:
                    return default
            if isinstance(session, dict):
                try:
                    return float(session.get(key, default))
                except Exception:
                    return default
            return default

        breakdown: dict[str, float] = {}
        score = 0.0
        for feature, weight in weights.items():
            value = read_feature(feature, 0.0)
            if feature == "topic_match":
                value = self._topic_affinity(session, user_profile)
            elif feature == "locality_match":
                value = self._locality_affinity(session, user_profile)
            part = float(value) * float(weight)
            breakdown[feature] = part
            score += part

        score = round(score, 4)
        if return_breakdown:
            return score, breakdown
        return score

    def _topic_affinity(self, session: Any, user_profile: dict[str, Any]) -> float:
        topics = getattr(session, "topics", None)
        if topics is None and isinstance(session, dict):
            topics = session.get("topics") or session.get("topic")
        if not topics:
            return 0.0
        if isinstance(topics, str):
            topics = [topics]
        categories = user_profile.get("categories") or {}
        if not isinstance(categories, dict):
            return 0.0
        return float(max([categories.get(topic, 0.0) for topic in topics] or [0.0]))

    def _locality_affinity(self, session: Any, user_profile: dict[str, Any]) -> float:
        location = getattr(session, "location", None)
        if location is None and isinstance(session, dict):
            location = session.get("location")
        locations = user_profile.get("locations") or {}
        if not location or not isinstance(locations, dict):
            return 0.0
        try:
            return float(min(float(locations.get(location, 0.0)) / 10.0, 1.0))
        except Exception:
            return 0.0

    def get_recommended_live(self, user_id: int):
        """
        Placeholder für echte Live-Recommendations (noch nicht produktiv).
        """
        return []


live_service = LiveService()

