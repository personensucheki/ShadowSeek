"""
Ranking-Service: Scoring und Sortierung von Posts und Livestreams
"""

class RankingService:
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
