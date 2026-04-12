"""
Recommendation-Service: Kandidatenauswahl und Re-Ranking (Feed/Live).

Realitätsstatus:
- Der Feed-Subsystem ist im Repo sichtbar, aber nicht vollständig in produktive Flows integriert.
- Dieses Modul bietet daher eine **stabile, defensive** Implementierung, die den App-Start nicht bricht
  und klar signalisiert, dass echte Recommendations noch ausgebaut werden müssen.
"""

from __future__ import annotations

import logging
from typing import Any

from app.config_feed import FEED_CONFIG
from app.services.live_service import live_service
from app.services.ranking_service import ranking_service


class RecommendationService:
    def __init__(self) -> None:
        log_level = FEED_CONFIG.get("LOG_LEVEL", "INFO")
        self.logger = logging.getLogger("RecommendationService")
        self.logger.setLevel(getattr(logging, str(log_level).upper(), logging.INFO))

    def get_feed(
        self,
        user_id: int,
        *,
        feed_type: str = "discovery",
        session_state: dict[str, Any] | None = None,
        debug: bool = False,
    ) -> dict[str, Any]:
        """
        Stabiler Placeholder für Feed Recommendations.

        Returns:
          - items: list (leer solange nicht integriert)
          - meta: dict (Status/Hint)
        """
        self.logger.info("Feed requested user=%s type=%s", user_id, feed_type)
        return {
            "items": [],
            "meta": {
                "enabled": False,
                "reason": "Recommendation pipeline not integrated yet.",
            },
        }

    def score_feed_candidates(
        self,
        user_id: int,
        candidates: list[Any],
        *,
        user_profile: dict[str, Any] | None = None,
        session_state: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Utility: Score candidates using local ranking_service (no external calls).
        """
        user_profile = user_profile or {}
        scored: list[dict[str, Any]] = []
        for cand in candidates:
            try:
                score, breakdown = ranking_service.score_feed_candidate(
                    cand, user_profile, session_state, return_breakdown=True
                )
            except Exception:
                score, breakdown = 0.0, {}
            scored.append({"candidate": cand, "score": score, "breakdown": breakdown})
        return sorted(scored, key=lambda item: item["score"], reverse=True)

    def score_live_candidates(
        self,
        user_id: int,
        candidates: list[Any],
        *,
        user_profile: dict[str, Any] | None = None,
        session_state: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        user_profile = user_profile or {}
        scored: list[dict[str, Any]] = []
        for cand in candidates:
            try:
                score, breakdown = live_service.score_live_candidate(
                    cand, user_profile, session_state, return_breakdown=True
                )
            except Exception:
                score, breakdown = 0.0, {}
            scored.append({"candidate": cand, "score": score, "breakdown": breakdown})
        return sorted(scored, key=lambda item: item["score"], reverse=True)


recommendation_service = RecommendationService()

