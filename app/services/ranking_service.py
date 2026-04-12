"""
Ranking-Service: Scoring und Sortierung von Posts und Livestreams
"""

from app.config_feed import FEED_CONFIG

class RankingService:

        def score_feed_candidate(self, candidate, user_profile, session_state=None, return_breakdown=False):
            """
            Berechnet den gewichteten Feed-Score nach Formel und gibt optional Breakdown zurück.
            """
            weights = FEED_CONFIG.get("FEED_SCORE_WEIGHTS", {
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
            })
            # Defensive: Hole alle Features, setze Defaults
            f = lambda key, default=0.0: getattr(candidate, key, candidate.get(key, default)) if hasattr(candidate, key) or isinstance(candidate, dict) else default
            breakdown = {}
            score = 0.0
            for feat, w in weights.items():
                val = f(feat, 0.0)
                # Optional: Spezialbehandlung für Affinitäten
                if feat == "topic_match":
                    val = self._topic_affinity(candidate, user_profile)
                elif feat == "creator_affinity":
                    val = self._creator_affinity(candidate, user_profile)
                elif feat == "locality_match":
                    val = self._locality_affinity(candidate, user_profile)
                breakdown[feat] = val * w
                score += val * w
            if return_breakdown:
                return round(score, 4), breakdown
            return round(score, 4)

        def _topic_affinity(self, candidate, user_profile):
            # Platzhalter: Berechne Themenaffinität
            topics = getattr(candidate, 'topics', getattr(candidate, 'topic', []))
            if not topics:
                return 0.0
            profile = user_profile.get('categories', {})
            if isinstance(topics, str):
                topics = [topics]
            return max([profile.get(t, 0.0) for t in topics if t in profile] or [0.0])

        def _creator_affinity(self, candidate, user_profile):
            # Platzhalter: Berechne Creator-Affinität
            creator_id = getattr(candidate, 'creator_id', None)
            profile = user_profile.get('creators', {})
            if creator_id and creator_id in profile:
                return min(profile[creator_id] / 10.0, 1.0)
            return 0.0

        def _locality_affinity(self, candidate, user_profile):
            # Platzhalter: Berechne Lokalitätsaffinität
            location = getattr(candidate, 'location', None)
            profile = user_profile.get('locations', {})
            if location and location in profile:
                return min(profile[location] / 10.0, 1.0)
            return 0.0
    def score_post(self, post, metrics, user_profile):
        """
        Berechnet einen heuristischen Score für einen Post.
        Berücksichtigt: watch_time, completion_rate, rewatch_rate, shares, saves, comments_quality,
        profile_click_rate, follow_conversion, skip_rate, report_rate, freshness_bonus, creator_diversity_bonus, exploration_bonus
        """
        score = 0.0
        # Engagement
        score += 2.0 * metrics.get('watch_time_seconds', 0) / max(metrics.get('duration', 1), 1)
        score += 1.5 * metrics.get('completion_rate', 0)
        score += 1.2 * metrics.get('rewatch_rate', 0)
        score += 1.0 * metrics.get('shares', 0)
        score += 0.8 * metrics.get('saves', 0)
        score += 0.7 * metrics.get('comments_quality', 0)
        score += 0.6 * metrics.get('profile_click_rate', 0)
        score += 0.6 * metrics.get('follow_conversion', 0)
        score -= 1.0 * metrics.get('skip_rate', 0)
        score -= 1.5 * metrics.get('report_rate', 0)
        # Boni
        score += 0.5 * metrics.get('freshness_bonus', 0)
        score += 0.3 * metrics.get('creator_diversity_bonus', 0)
        score += 0.2 * metrics.get('exploration_bonus', 0)
        return round(score, 4)

    def score_live(self, session, metrics, user_profile):
        """
        Berechnet einen heuristischen Score für eine Live-Session.
        Berücksichtigt: viewer_growth_rate, avg_watch_time, chat_activity, retention_3min, creator_loyalty_score, quality_score, recency
        """
        score = 0.0
        score += 2.0 * metrics.get('viewer_growth_rate', 0)
        score += 1.5 * metrics.get('avg_watch_time', 0)
        score += 1.2 * metrics.get('chat_activity', 0)
        score += 1.0 * metrics.get('retention_3min', 0)
        score += 1.0 * metrics.get('creator_loyalty_score', 0)
        score += 0.8 * metrics.get('quality_score', 0)
        score += 0.5 * metrics.get('recency', 0)
        return round(score, 4)

ranking_service = RankingService()
