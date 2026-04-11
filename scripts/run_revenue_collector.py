import os
import time
import logging
from app import app
from app.services.revenue_live_collector import RevenueLiveCollector
from app.extensions import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERVAL = int(os.getenv("REVENUE_COLLECTOR_INTERVAL", "60"))

def main():
    with app.app_context():
        collector = RevenueLiveCollector(db.session)
        logger.info("Revenue Collector gestartet. Intervall: %s Sekunden", INTERVAL)
        while True:
            try:
                collector.run_once()
            except KeyboardInterrupt:
                logger.info("Collector gestoppt.")
                break
            except Exception as exc:
                logger.exception("Collector-Loop Fehler: %s", exc)
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
