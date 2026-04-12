"""
Ranking-Service: lokales Scoring und Sortierung für Feed-Kandidaten.

Dieses Modul ist absichtlich defensiv:
- Es soll den App-Start nicht brechen, auch wenn Feed/Ranking noch ausgebaut wird.
"""

from __future__ import annotations

from typing import Any

from app.config_feed import FEED_CONFIG


class RankingService:
    @staticmethod
    def rank_results(results: list[dict], username_variants: list[str] | None = None, providers: list[str] | None = None):
        """
        Backwards-compatible ranking helper for OSINT/search core tests.

        The input `results` is a list of dicts with optional fields like:
          - raw_confidence_hint (0..1)
          - evidence_count (int)
          - provider (slug)
          - username

        Returns: same list with added `score` (0..100) and `confidence` (high/medium/low).
        """
        username_variants = [str(v).strip().lower() for v in (username_variants or []) if str(v).strip()]
        providers = [str(p).strip().lower() for p in (providers or []) if str(p).strip()]

        ranked: list[dict] = []
        for item in results or []:
            raw = dict(item or {})
            provider = str(raw.get("provider") or "").strip().lower()
            username = str(raw.get("username") or "").strip().lower()

            base = float(raw.get("raw_confidence_hint") or 0.0) * 70.0
            evidence = float(raw.get("evidence_count") or 0) * 8.0
            provider_boost = 5.0 if (provider and (not providers or provider in providers)) else 0.0
            username_boost = 10.0 if (username and username_variants and username in username_variants) else 0.0

            score = max(0.0, min(100.0, base + evidence + provider_boost + username_boost))
            raw["score"] = round(score, 2)
            raw["confidence"] = "high" if score >= 85 else "medium" if score >= 60 else "low"
            ranked.append(raw)

        ranked.sort(key=lambda r: r.get("score", 0), reverse=True)
        return ranked

    def score_feed_candidate(
        self,
        candidate: Any,
        user_profile: dict | None,
        session_state: dict | None = None,
        *,
        return_breakdown: bool = False,
    ):
        user_profile = user_profile or {}
        weights = FEED_CONFIG.get(
            "FEED_SCORE_WEIGHTS",
            {
                "predicted_watchtime": 0.22,
                "completion_rate": 0.16,
                "rewatch_rate": 0.11,
                "share_rate": 0.10,
                "save_rate": 0.07,
                "comment_quality": 0.06,
                "profile_click_rate": 0.06,
                "follow_conversion_rate": 0.07,
                "topic_match": 0.05,
                "creator_affinity": 0.04,
                "locality_match": 0.03,
                "freshness": 0.03,
                "exploration_bonus": 0.04,
                "skip_rate": -0.18,
                "report_rate": -0.22,
                "duplicate_penalty": -0.12,
                "spam_penalty": -0.10,
            },
        )

        def read_feature(key: str, default: float = 0.0) -> float:
            if hasattr(candidate, key):
                try:
                    return float(getattr(candidate, key))
                except Exception:
                    return default
            if isinstance(candidate, dict):
                try:
                    return float(candidate.get(key, default))
                except Exception:
                    return default
            return default

        def topic_affinity() -> float:
            topics = getattr(candidate, "topics", None)
            if topics is None and isinstance(candidate, dict):
                topics = candidate.get("topics") or candidate.get("topic")
            if not topics:
                return 0.0
            if isinstance(topics, str):
                topics = [topics]
            categories = user_profile.get("categories") or {}
            if not isinstance(categories, dict):
                return 0.0
            return float(max([categories.get(topic, 0.0) for topic in topics] or [0.0]))

        def creator_affinity() -> float:
            creator_id = getattr(candidate, "creator_id", None)
            if creator_id is None and isinstance(candidate, dict):
                creator_id = candidate.get("creator_id")
            creators = user_profile.get("creators") or {}
            if not creator_id or not isinstance(creators, dict):
                return 0.0
            try:
                return float(min(float(creators.get(creator_id, 0.0)) / 10.0, 1.0))
            except Exception:
                return 0.0

        def locality_affinity() -> float:
            location = getattr(candidate, "location", None)
            if location is None and isinstance(candidate, dict):
                location = candidate.get("location")
            locations = user_profile.get("locations") or {}
            if not location or not isinstance(locations, dict):
                return 0.0
            try:
                return float(min(float(locations.get(location, 0.0)) / 10.0, 1.0))
            except Exception:
                return 0.0

        breakdown: dict[str, float] = {}
        score = 0.0
        for feature, weight in weights.items():
            value = read_feature(feature, 0.0)
            if feature == "topic_match":
                value = topic_affinity()
            elif feature == "creator_affinity":
                value = creator_affinity()
            elif feature == "locality_match":
                value = locality_affinity()
            part = float(value) * float(weight)
            breakdown[feature] = part
            score += part

        score = round(score, 4)
        if return_breakdown:
            return score, breakdown
        return score


ranking_service = RankingService()
