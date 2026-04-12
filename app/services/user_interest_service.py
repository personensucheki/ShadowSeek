"""
User-Interest-Service: Interessenprofil pro User
"""

import logging
from collections import defaultdict
from app.config_feed import FEED_CONFIG

# In-Memory-Profil für Demo-Zwecke (Produktiv: DB-Modell)
_user_interest_profiles = defaultdict(lambda: {"categories": {}, "hashtags": {}, "creators": {}, "locations": {}})

class UserInterestService:
    def __init__(self):
        self.log_level = FEED_CONFIG.get("LOG_LEVEL", "INFO")
        self.logger = logging.getLogger("UserInterestService")
        self.logger.setLevel(getattr(logging, self.log_level, logging.INFO))
    def update_user_interest_profile(self, user_id, interaction):
        if not user_id:
            self.logger.warning("update_user_interest_profile: user_id fehlt oder leer")
            return
        if not interaction:
            self.logger.warning("update_user_interest_profile: interaction fehlt oder None")
            return
        """
        Aktualisiert das Interessenprofil eines Users anhand einer Interaktion.
        Berücksichtigt: Kategorien, Hashtags, Creator, Location, Watchtime
        """
        try:
            profile = _user_interest_profiles[user_id]
            meta = getattr(interaction, 'meta', {}) or {}
            # Kategorien zählen
            for cat in meta.get('categories', []):
                if not isinstance(cat, str):
                    self.logger.debug(f"Ignoriere ungültige Kategorie: {cat}")
                    continue
                profile['categories'][cat] = profile['categories'].get(cat, 0) + 1
            # Hashtags gewichten
            for tag in meta.get('hashtags', []):
                if not isinstance(tag, str):
                    self.logger.debug(f"Ignoriere ungültigen Hashtag: {tag}")
                    continue
                profile['hashtags'][tag] = profile['hashtags'].get(tag, 0) + 1
            # Creator-Affinität
            creator_id = meta.get('creator_id')
            if creator_id:
                profile['creators'][creator_id] = profile['creators'].get(creator_id, 0) + 1
            # Location
            location = meta.get('location')
            if location:
                profile['locations'][location] = profile['locations'].get(location, 0) + 1
            # Watchtime
            wt = meta.get('watch_time_seconds', 0)
            if not isinstance(wt, (int, float)):
                self.logger.debug(f"Ungültige watch_time_seconds: {wt}")
                wt = 0
            profile['watch_time'] = profile.get('watch_time', 0) + wt
            self.logger.debug(f"Profil für User {user_id} aktualisiert: {profile}")
        except Exception as e:
            self.logger.error(f"Fehler beim Update des User-Interest-Profils: {e}")

    def get_user_interest_profile(self, user_id):
        if not user_id:
            self.logger.warning("get_user_interest_profile: user_id fehlt oder leer")
            return {}
        """
        Gibt das aktuelle Interessenprofil zurück.
        """
        return _user_interest_profiles[user_id]

user_interest_service = UserInterestService()
