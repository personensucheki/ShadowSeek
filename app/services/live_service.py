"""
Live-Service: Verwaltung und Scoring von Livestreams
"""

from app.config_feed import FEED_CONFIG

class LiveService:

        def score_live_candidate(self, session, user_profile, session_state=None, return_breakdown=False):
            """
            Bewertet eine Live-Session nach gewichteter Formel, gibt Score und Breakdown zurück.
            """
            weights = FEED_CONFIG.get("LIVE_SCORE_WEIGHTS", {
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
            })
            f = lambda key, default=0.0: getattr(session, key, session.get(key, default)) if hasattr(session, key) or isinstance(session, dict) else default
            breakdown = {}
            score = 0.0
            for feat, w in weights.items():
                val = f(feat, 0.0)
                # Affinitäten
                if feat == "topic_match":
                    val = self._topic_affinity(session, user_profile)
                elif feat == "locality_match":
                    val = self._locality_affinity(session, user_profile)
                breakdown[feat] = val * w
                score += val * w
            if return_breakdown:
                return round(score, 4), breakdown
            return round(score, 4)

        def _topic_affinity(self, session, user_profile):
            topics = getattr(session, 'topics', getattr(session, 'topic', []))
            if not topics:
                return 0.0
            profile = user_profile.get('categories', {})
            if isinstance(topics, str):
                topics = [topics]
            return max([profile.get(t, 0.0) for t in topics if t in profile] or [0.0])

        def _locality_affinity(self, session, user_profile):
            location = getattr(session, 'location', None)
            profile = user_profile.get('locations', {})
            if location and location in profile:
                return min(profile[location] / 10.0, 1.0)
            return 0.0
    def get_recommended_live(self, user_id):
        # TODO: Kandidaten holen und scoren
        return []

    def live_score(self, session, metrics, user_profile):
        # TODO: Heuristik implementieren
        return 0.0

live_service = LiveService()
