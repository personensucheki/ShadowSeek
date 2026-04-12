"""
Live-Service: Verwaltung und Scoring von Livestreams
"""

class LiveService:
    def get_recommended_live(self, user_id):
        # TODO: Kandidaten holen und scoren
        return []

    def live_score(self, session, metrics, user_profile):
        # TODO: Heuristik implementieren
        return 0.0

live_service = LiveService()
