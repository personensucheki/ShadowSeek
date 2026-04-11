import logging
from app.services.revenue_provider_registry import get_revenue_providers
from datetime import datetime

logger = logging.getLogger(__name__)

class RevenueLiveCollector:
    def __init__(self, db_session):
        self.db_session = db_session

    def run_once(self):
        providers = get_revenue_providers()
        total_saved = 0
        for provider in providers:
            loaded = 0
            saved = 0
            skipped = 0
            errors = 0
            try:
                rows = provider.fetch()
                loaded = len(rows) if rows else 0
                if not rows:
                    logger.info("Provider %s lieferte keine Daten", provider.name)
                    continue
                for row in rows:
                    try:
                        result = self.save_revenue_row(row)
                        if result:
                            saved += 1
                        else:
                            skipped += 1
                    except Exception as exc:
                        logger.exception("Fehler beim Speichern eines Rows: %s", exc)
                        errors += 1
                total_saved += saved
                logger.info(
                    "Provider: %s | Records geladen: %d | Neu gespeichert: %d | Übersprungen (duplicate): %d | Fehler: %d",
                    provider.name, loaded, saved, skipped, errors
                )
            except Exception as exc:
                logger.exception("Provider %s Fehler: %s", provider.name, exc)
        logger.info("Collector-Lauf beendet. Gesamt gespeichert: %s", total_saved)
        return total_saved

    def save_revenue_row(self, row):
        # Row validieren, als RevenueEvent speichern, committen
        from app.models.revenue import RevenueEvent
        try:
            # Nur speichern, wenn estimated_revenue > 0 und Pflichtfelder vorhanden
            est = row.get("estimated_revenue")
            if est is None or not isinstance(est, (int, float)) or est <= 0:
                logger.info("Row übersprungen: Kein positiver Umsatz: %s", row)
                return False
            username = row.get("username")
            platform = row.get("platform")
            captured_at = row.get("captured_at")
            source = row.get("source")
            if not username or not platform or not captured_at:
                logger.info("Row übersprungen: Pflichtfeld fehlt: %s", row)
                return False
            # captured_at ggf. parsen
            from datetime import datetime
            if isinstance(captured_at, str):
                try:
                    captured_at = datetime.fromisoformat(captured_at)
                except Exception:
                    logger.info("Row übersprungen: captured_at nicht parsbar: %s", row)
                    return False
            # Deduplizierung: Existiert bereits?
            exists = self.db_session.query(RevenueEvent).filter_by(
                platform=platform,
                username=username,
                captured_at=captured_at,
                source=source
            ).first()
            if exists:
                logger.info("Row übersprungen: Duplikat erkannt: %s", row)
                return False
            event = RevenueEvent(
                platform=platform,
                username=username,
                display_name=row.get("display_name"),
                estimated_revenue=est,
                currency=row.get("currency", "EUR"),
                diamonds=row.get("diamonds"),
                followers=row.get("followers"),
                source=source,
                confidence=row.get("confidence"),
                captured_at=captured_at,
            )
            self.db_session.add(event)
            self.db_session.commit()
            logger.info("Revenue gespeichert: %s/%s %.2f", platform, username, est)
            return True
        except Exception as exc:
            logger.exception("Fehler beim Speichern: %s", exc)
            self.db_session.rollback()
            return False
