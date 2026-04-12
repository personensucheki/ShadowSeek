"""
Recommendation-Service: Kandidatenauswahl und Re-Ranking
"""


import logging
from app.config_feed import FEED_CONFIG
from app.services.ranking_service import ranking_service
from app.services.live_service import live_service
from app.services.user_interest_service import user_interest_service
from app.services.moderation_service import moderation_service
# Optional: from app.services.session_state_service import session_state_service

class RecommendationService:
            def apply_anti_spam_risk(self, candidates):
                """
                Anti-Spam/Risk-Hooks: Penalty für verdächtige Engagement-Spikes, Duplikate, Risk-Score, View-Farming, etc.
                """
                for c in candidates:
                    cand = c["candidate"]
                    score = c["score"]
                    # Engagement-Spikes
                    if getattr(cand, "engagement_spike", False):
                        score -= 0.15
                    # Duplicate Marker
                    if getattr(cand, "duplicate_marker", False):
                        score -= 0.2
                    # Risk-Score
                    if getattr(cand, "risk_score", 0.0) > 0.7:
                        score -= 0.25
                    # View-Farming
                    if getattr(cand, "is_view_farming", False):
                        score -= 0.2
                    # Bot-Kommentare
                    if getattr(cand, "bot_comment_ratio", 0.0) > 0.5:
                        score -= 0.1
                    c["score"] = score
                self.logger.debug("Anti-Spam/Risk-Hooks angewendet.")
                return candidates
        def apply_cold_start(self, candidates):
            """
            Cold-Start-Strategie: Für neue Kandidaten ohne Nutzersignale werden Scores aus Content-Merkmalen geschätzt.
            """
            for c in candidates:
                cand = c["candidate"]
                # Beispiel: Score-Boost für hohe Medienqualität, relevante Hashtags, Sprache, Standort
                score = c["score"]
                if getattr(cand, "is_new", False):
                    # Medienqualität
                    quality = getattr(cand, "media_quality", 0.5)
                    score += 0.1 * quality
                    # Hashtags/Auto-Tags
                    hashtags = getattr(cand, "hashtags", [])
                    if "trending" in hashtags:
                        score += 0.05
                    # Sprache
                    if getattr(cand, "language", "") == "de":
                        score += 0.03
                    # Standort
                    if getattr(cand, "location", None):
                        score += 0.02
                    # Caption-Länge
                    caption = getattr(cand, "caption", "")
                    if len(caption) > 40:
                        score += 0.02
                c["score"] = score
            self.logger.debug("Cold-Start-Strategie angewendet.")
            return candidates
    def __init__(self):
        self.log_level = FEED_CONFIG.get("LOG_LEVEL", "INFO")
        self.logger = logging.getLogger("RecommendationService")
        self.logger.setLevel(getattr(logging, self.log_level, logging.INFO))

    # --- PIPELINE ENTRYPOINTS ---
    def get_feed(self, user_id, feed_type="discovery", session_state=None, debug=False):
        """
        Hauptpipeline für Feed-Empfehlungen.
        """
        self.logger.info(f"Starte Feed-Pipeline für user={user_id} type={feed_type}")
        # 1. Candidate Retrieval
        candidates = self.candidate_retrieval(user_id, feed_type, session_state)
        self.logger.debug(f"Kandidaten nach Retrieval: {len(candidates)}")
        # 2. Hard Filters
        candidates = self.apply_hard_filters(user_id, candidates, session_state)
        self.logger.debug(f"Kandidaten nach Hard Filters: {len(candidates)}")
        # 3. Base Scoring
        scored = self.score_candidates(user_id, candidates, session_state)
        # 4. Cold-Start-Strategie
        scored = self.apply_cold_start(scored)
        # 5. Exploration
        scored = self.apply_exploration(user_id, scored, session_state)
        # 6. Anti-Spam/Risk-Hooks
        scored = self.apply_anti_spam_risk(scored)
        # 7. Session Adjustments
        scored = self.apply_session_adjustments(user_id, scored, session_state)
        # 8. Diversity Re-Ranking
        final_list = self.diversity_rerank(user_id, scored, session_state)
        # 7. Limit & Return
        max_items = FEED_CONFIG.get("MAX_FEED_ITEMS", 50)
        result = final_list[:max_items]
        if debug:
            # Score Breakdown und Entscheidungsweg für Debug-Zwecke
            debug_items = []
            for c in result:
                item = {
                    "candidate": c["candidate"],
                    "score": c["score"],
                    "breakdown": c.get("breakdown", {}),
                }
                debug_items.append(item)
            return debug_items
        return [c["candidate"] for c in result]

    def get_live_recommendations(self, user_id, session_state=None, debug=False):
        """
        Hauptpipeline für Live-Empfehlungen.
        """
        self.logger.info(f"Starte Live-Pipeline für user={user_id}")
        candidates = self.live_candidate_retrieval(user_id, session_state)
        candidates = self.apply_live_hard_filters(user_id, candidates, session_state)
        scored = self.score_live_candidates(user_id, candidates, session_state)
        scored = self.apply_live_session_adjustments(user_id, scored, session_state)
        final_list = self.live_diversity_rerank(user_id, scored, session_state)
        max_items = FEED_CONFIG.get("MAX_LIVE_ITEMS", 20)
        result = final_list[:max_items]
        if debug:
            return result
        return [c["candidate"] for c in result]

    # --- PIPELINE STAGES ---
    def candidate_retrieval(self, user_id, feed_type, session_state):
        """
        Kandidaten aus mehreren Pools zusammenführen.
        Pool-Anteile konfigurierbar, robust gegen leere Pools.
        """
        # Pool-Konfiguration (z.B. 30% Interessen, 20% Following, ...)
        pool_config = FEED_CONFIG.get("CANDIDATE_POOLS", {
            "interests": 0.3,
            "following": 0.2,
            "trends": 0.2,
            "local": 0.15,
            "exploration": 0.15
        })
        max_candidates = FEED_CONFIG.get("MAX_FEED_CANDIDATES", 200)

        # 1. Interests
        interest_candidates = self.get_interest_candidates(user_id, session_state)
        # 2. Following
        following_candidates = self.get_following_candidates(user_id, session_state)
        # 3. Trends
        trend_candidates = self.get_trend_candidates(user_id, session_state)
        # 4. Local
        local_candidates = self.get_local_candidates(user_id, session_state)
        # 5. Exploration
        exploration_candidates = self.get_exploration_candidates(user_id, session_state)

        # Pool-Mix
        pools = [
            (interest_candidates, pool_config.get("interests", 0.3)),
            (following_candidates, pool_config.get("following", 0.2)),
            (trend_candidates, pool_config.get("trends", 0.2)),
            (local_candidates, pool_config.get("local", 0.15)),
            (exploration_candidates, pool_config.get("exploration", 0.15)),
        ]
        candidates = []
        for pool, weight in pools:
            n = int(max_candidates * weight)
            candidates.extend(pool[:n])
        # Fallback: auffüllen falls zu wenig
        if len(candidates) < max_candidates:
            all_pools = interest_candidates + following_candidates + trend_candidates + local_candidates + exploration_candidates
            seen = set(id(c) for c in candidates)
            for c in all_pools:
                if id(c) not in seen:
                    candidates.append(c)
                if len(candidates) >= max_candidates:
                    break
        self.logger.debug(f"Candidate Retrieval: {len(candidates)} Kandidaten gesammelt.")
        return candidates

    def get_interest_candidates(self, user_id, session_state):
        """Kandidaten nach User-Interessenprofil (Platzhalter)."""
        # TODO: Implementiere echtes Retrieval
        return []

    def get_following_candidates(self, user_id, session_state):
        """Kandidaten von gefolgten Usern (Platzhalter)."""
        # TODO: Implementiere echtes Retrieval
        return []

    def get_trend_candidates(self, user_id, session_state):
        """Aktuelle Trend-Kandidaten (Platzhalter)."""
        # TODO: Implementiere echtes Retrieval
        return []

    def get_local_candidates(self, user_id, session_state):
        """Kandidaten aus derselben Region/Sprache (Platzhalter)."""
        # TODO: Implementiere echtes Retrieval
        return []

    def get_exploration_candidates(self, user_id, session_state):
        """Neue Creator/Themen für Exploration (Platzhalter)."""
        # TODO: Implementiere echtes Retrieval
        return []

    def live_candidate_retrieval(self, user_id, session_state):
        """Kandidaten für Live-Empfehlungen holen (Pools: following, interests, trends, local, exploration, live)."""
        # TODO: Analog zu Feed, aber für Live
        return []

    def apply_hard_filters(self, user_id, candidates, session_state):
        """
        Filtere geblockte User, gemeldete Inhalte, NSFW, Spam, Duplikate, Wiederholungen, Sprache.
        Platzhalter: Filterlogik kann später mit echten Daten/Modellen ergänzt werden.
        """
        filtered = []
        blocked_users = self.get_blocked_users(user_id)
        seen_posts = self.get_seen_posts(user_id, session_state)
        for c in candidates:
            # Annahme: c ist ein Dict oder Objekt mit Attributen
            if hasattr(c, 'creator_id') and c.creator_id in blocked_users:
                continue
            if hasattr(c, 'post_id') and c.post_id in seen_posts:
                continue
            # Moderation: Spam, NSFW, Risk, Duplicate
            if hasattr(c, 'risk_score') and c.risk_score > 0.8:
                continue
            if hasattr(c, 'nsfw_score') and c.nsfw_score > 0.7:
                continue
            if hasattr(c, 'duplicate_marker') and c.duplicate_marker:
                continue
            if hasattr(c, 'language') and not self.is_language_allowed(user_id, c.language):
                continue
            # Optional: weitere Filter (z.B. gemeldet, shadowban)
            filtered.append(c)
        self.logger.debug(f"Hard Filters: {len(filtered)}/{len(candidates)} Kandidaten übrig.")
        return filtered

    def get_blocked_users(self, user_id):
        """Hole blockierte User für den aktuellen User (Platzhalter)."""
        # TODO: Echte Blockliste aus DB
        return set()

    def get_seen_posts(self, user_id, session_state):
        """Hole bereits gesehene Posts (Platzhalter, z.B. aus Session oder DB)."""
        # TODO: Echte Historie
        return set()

    def is_language_allowed(self, user_id, language):
        """Prüfe, ob Sprache für User zulässig ist (Platzhalter)."""
        # TODO: User-Präferenzen prüfen
        return True

    def score_candidates(self, user_id, candidates, session_state):
        """
        Berechne Score pro Kandidat (Feed) mit ranking_service.
        Gibt Liste von Dicts mit Score und optional Breakdown zurück.
        """
        user_profile = user_interest_service.get_user_interest_profile(user_id)
        scored = []
        for c in candidates:
            try:
                score, breakdown = ranking_service.score_feed_candidate(c, user_profile, session_state, return_breakdown=True)
            except Exception as e:
                self.logger.error(f"Scoring-Fehler für Kandidat: {e}")
                score, breakdown = 0.0, {}
            scored.append({"candidate": c, "score": score, "breakdown": breakdown})
        self.logger.debug(f"Feed-Scoring: {len(scored)} Kandidaten gescored.")
        return scored

    def apply_exploration(self, user_id, scored_candidates, session_state):
        """
        Füge Exploration-Slots hinzu (neue Creator/Themen). Verhältnis konfigurierbar.
        Exploration-Kandidaten werden gezielt untergemischt.
        """
        exploration_ratio = FEED_CONFIG.get("EXPLORATION_RATIO", 0.2)  # z.B. 0.2 = 20%
        n_total = len(scored_candidates)
        n_explore = max(1, int(n_total * exploration_ratio))
        # Exploration-Kandidaten: Score < 0.5 oder explizit markiert
        exploration = [c for c in scored_candidates if getattr(c["candidate"], "is_exploration", False)]
        # Fallback: Kandidaten mit niedrigem topic/creator/locality-Affinity
        if len(exploration) < n_explore:
            exploration += [c for c in scored_candidates if c["score"] < 0.5 and c not in exploration]
        # Limitieren
        exploration = exploration[:n_explore]
        # Sichere Treffer
        safe = [c for c in scored_candidates if c not in exploration]
        # Mischen: 4 sichere, 1 Exploration (oder nach Verhältnis)
        result = []
        safe_idx, exp_idx = 0, 0
        chunk = max(1, int((1.0 - exploration_ratio) / exploration_ratio))
        while safe_idx < len(safe) or exp_idx < len(exploration):
            for _ in range(chunk):
                if safe_idx < len(safe):
                    result.append(safe[safe_idx])
                    safe_idx += 1
            if exp_idx < len(exploration):
                result.append(exploration[exp_idx])
                exp_idx += 1
        self.logger.debug(f"Exploration: {len(exploration)} Exploration-Kandidaten untergemischt.")
        return result[:n_total]

    def apply_session_adjustments(self, user_id, scored_candidates, session_state):
        """
        Passe Scores anhand aktueller Session-Signale an.
        Beispiele: User schaut aktuell mehr Lives, skippt Fotos, schaut bestimmtes Thema, klickt lokale Inhalte.
        """
        if not session_state:
            return scored_candidates
        # Beispielhafte Session-Signale
        prefer_live = session_state.get("prefer_live", False)
        skip_photos = session_state.get("skip_photos", False)
        boost_topic = session_state.get("boost_topic")
        boost_local = session_state.get("boost_local", False)
        adjusted = []
        for c in scored_candidates:
            score = c["score"]
            cand = c["candidate"]
            # Live-Boost
            if prefer_live and getattr(cand, "content_type", None) == "live":
                score += 0.2
            # Foto-Skip
            if skip_photos and getattr(cand, "content_type", None) == "photo":
                score -= 0.2
            # Themen-Boost
            if boost_topic:
                topics = getattr(cand, "topics", getattr(cand, "topic", []))
                if isinstance(topics, str):
                    topics = [topics]
                if boost_topic in topics:
                    score += 0.15
            # Lokal-Boost
            if boost_local and getattr(cand, "is_local", False):
                score += 0.1
            c_adj = dict(c)
            c_adj["score"] = score
            adjusted.append(c_adj)
        self.logger.debug("Session-Aware Anpassung angewendet.")
        return adjusted

    def diversity_rerank(self, user_id, scored_candidates, session_state):
        """
        Re-Ranking für Creator/Topic-Diversität, keine Monotonie.
        Maximal n Posts pro Creator, Themenmix, keine Wiederholungen direkt hintereinander.
        """
        max_per_creator = FEED_CONFIG.get("MAX_CREATOR_PER_FEED", 3)
        max_topic_repeat = FEED_CONFIG.get("MAX_TOPIC_REPEAT", 2)
        result = []
        creator_count = {}
        topic_count = {}
        last_creator = None
        last_topic = None
        for c in sorted(scored_candidates, key=lambda x: x["score"], reverse=True):
            cand = c["candidate"]
            creator = getattr(cand, "creator_id", None)
            topics = getattr(cand, "topics", getattr(cand, "topic", []))
            if isinstance(topics, str):
                topics = [topics]
            # Creator-Limit
            if creator:
                if creator_count.get(creator, 0) >= max_per_creator:
                    continue
            # Themen-Limit
            main_topic = topics[0] if topics else None
            if main_topic:
                if topic_count.get(main_topic, 0) >= max_topic_repeat:
                    continue
            # Keine Wiederholung direkt hintereinander
            if creator and creator == last_creator:
                continue
            if main_topic and main_topic == last_topic:
                continue
            # Übernehmen
            result.append(c)
            if creator:
                creator_count[creator] = creator_count.get(creator, 0) + 1
                last_creator = creator
            if main_topic:
                topic_count[main_topic] = topic_count.get(main_topic, 0) + 1
                last_topic = main_topic
            if len(result) >= FEED_CONFIG.get("MAX_FEED_ITEMS", 50):
                break
        self.logger.debug(f"Diversity Re-Ranking: {len(result)} Kandidaten nach Diversität.")
        return result

    # --- LIVE PIPELINE STAGES ---
    def live_candidate_retrieval(self, user_id, session_state):
        """Kandidaten für Live-Empfehlungen holen."""
        # TODO: Live-Pools
        return []

    def apply_live_hard_filters(self, user_id, candidates, session_state):
        """
        Filter für Live: inaktive/abgelaufene Streams, Risk, NSFW, Spam, Duplikate.
        Platzhalter: Filterlogik kann später mit echten Daten/Modellen ergänzt werden.
        """
        filtered = []
        for c in candidates:
            if hasattr(c, 'is_active') and not c.is_active:
                continue
            if hasattr(c, 'risk_score') and c.risk_score > 0.8:
                continue
            if hasattr(c, 'nsfw_score') and c.nsfw_score > 0.7:
                continue
            if hasattr(c, 'duplicate_marker') and c.duplicate_marker:
                continue
            # Optional: weitere Filter (z.B. gemeldet, shadowban)
            filtered.append(c)
        self.logger.debug(f"Live Hard Filters: {len(filtered)}/{len(candidates)} Kandidaten übrig.")
        return filtered

    def score_live_candidates(self, user_id, candidates, session_state):
        """
        Live-Scoring (siehe Live-Score-Formel in live_service.py).
        Gibt Liste von Dicts mit Score und Breakdown zurück.
        """
        user_profile = user_interest_service.get_user_interest_profile(user_id)
        scored = []
        for c in candidates:
            try:
                score, breakdown = live_service.score_live_candidate(c, user_profile, session_state, return_breakdown=True)
            except Exception as e:
                self.logger.error(f"Live-Scoring-Fehler: {e}")
                score, breakdown = 0.0, {}
            scored.append({"candidate": c, "score": score, "breakdown": breakdown})
        self.logger.debug(f"Live-Scoring: {len(scored)} Live-Kandidaten gescored.")
        return scored

    def apply_live_session_adjustments(self, user_id, scored_candidates, session_state):
        """Session-Awareness für Live."""
        # TODO: Live-Session-Logik
        return scored_candidates

    def live_diversity_rerank(self, user_id, scored_candidates, session_state):
        """Diversität für Live-Feed."""
        # TODO: Live-Diversity
        return sorted(scored_candidates, key=lambda x: x["score"], reverse=True)

recommendation_service = RecommendationService()
