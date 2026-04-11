
import sys
import os
import logging
import time

# Sicherstellen, dass das Projektverzeichnis im sys.path ist
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.services.revenue_live_collector import RevenueLiveCollector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTERVAL = int(os.getenv("REVENUE_COLLECTOR_INTERVAL", "60"))

def main():
    app = create_app()

    with app.app_context():
        collector = RevenueLiveCollector(db.session)
        logger.info(
            "Revenue Collector gestartet | Intervall: %s Sekunden",
            INTERVAL
        )
        while True:
            try:
                collector.run_once()
            except KeyboardInterrupt:
                logger.info("Collector gestoppt")
                break
            except Exception as exc:
                logger.exception("Collector Fehler: %s", exc)
            time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
