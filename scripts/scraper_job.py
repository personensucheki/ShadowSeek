import os
import time
import logging
from app.services.notify import send_telegram
from datetime import datetime
from threading import Thread
import requests
from bs4 import BeautifulSoup
from flask import current_app
from app.extensions import db
from app.models import EinnahmeInfo  # Modell für Einnahmen
from app.models.user import User
from app import create_app
from sqlalchemy.exc import SQLAlchemyError
from smtplib import SMTP

SCRAPER_URL = os.environ.get("SCRAPER_URL", "https://example.com/einnahmen")
SCRAPER_INTERVAL = int(os.environ.get("SCRAPER_INTERVAL", 86400))  # 24h
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def send_admin_notification(subject, message):
    try:
        # Dummy SMTP Beispiel, anpassen für produktiven Mailversand
        with SMTP("localhost") as smtp:
            smtp.sendmail("noreply@shadowseek.de", ADMIN_EMAIL, f"Subject: {subject}\n\n{message}")
    except Exception as e:
        logging.error(f"Fehler beim Senden der Admin-Mail: {e}")


def scrape_and_store():
    app = create_app()
    with app.app_context():
        try:
            logging.info(f"Starte Scraping von {SCRAPER_URL}")
            resp = requests.get(SCRAPER_URL, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            # TikTok Live Einnahmen extrahieren (z.B. wie Tikleap)
            einnahmen = []
            for row in soup.select("table.tiktok-live tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    # Annahme: [Zeit, User, Einnahme, Typ, Details]
                    zeitpunkt = datetime.strptime(cols[0].text.strip(), "%d.%m.%Y %H:%M")
                    quelle = cols[1].text.strip()
                    betrag = float(cols[2].text.replace("€", "").replace(",", ".").strip())
                    typ = cols[3].text.strip().lower()
                    details = cols[4].text.strip() if len(cols) > 4 else None
                    einnahmen.append({
                        "betrag": betrag,
                        "waehrung": "EUR",
                        "typ": typ,
                        "quelle": quelle,
                        "details": details,
                        "zeitpunkt": zeitpunkt
                    })
            # In DB speichern & Telegram-Benachrichtigung bei großen Einnahmen
            for eintrag in einnahmen:
                db.session.add(EinnahmeInfo(**eintrag))
                if eintrag["betrag"] >= 10:  # Schwelle für große Einnahme
                    msg = f"💸 Neue große Einnahme: {eintrag['betrag']:.2f} EUR von {eintrag['quelle']} ({eintrag['typ']}) am {eintrag['zeitpunkt'].strftime('%d.%m.%Y %H:%M')}\nDetails: {eintrag['details'] or '-'}"
                    send_telegram(msg)
            db.session.commit()
            logging.info(f"{len(einnahmen)} TikTok-Live Einnahmen gespeichert.")
        except Exception as e:
            logging.error(f"Scraping-Fehler: {e}")
            send_admin_notification("Scraping-Fehler", str(e))
            send_telegram(f"❗ Scraping-Fehler: {e}")


def scraper_job():
    while True:
        scrape_and_store()
        time.sleep(SCRAPER_INTERVAL)


def start_scraper_job():
    t = Thread(target=scraper_job, daemon=True)
    t.start()

# Optional: Trigger über Flask-CLI oder beim App-Start
if __name__ == "__main__":
    start_scraper_job()
    while True:
        time.sleep(3600)
