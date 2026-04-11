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
from app.services.revenue_events import event_from_legacy_row

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
            einnahmen = []
            # TikTok
            for row in soup.select("table.tiktok-live tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    zeitpunkt = datetime.strptime(cols[0].text.strip(), "%d.%m.%Y %H:%M")
                    quelle = cols[1].text.strip()
                    betrag = float(cols[2].text.replace("€", "").replace(",", ".").strip())
                    typ = cols[3].text.strip().lower()
                    details = cols[4].text.strip() if len(cols) > 4 else None
                    einnahmen.append({
                        "betrag": betrag,
                        "waehrung": "EUR",
                        "typ": f"tiktok_{typ}",
                        "quelle": quelle,
                        "details": details,
                        "zeitpunkt": zeitpunkt
                    })
            # Twitch
            for row in soup.select("table.twitch-live tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    zeitpunkt = datetime.strptime(cols[0].text.strip(), "%d.%m.%Y %H:%M")
                    quelle = cols[1].text.strip()
                    betrag = float(cols[2].text.replace("€", "").replace(",", ".").strip())
                    typ = cols[3].text.strip().lower()
                    details = cols[4].text.strip() if len(cols) > 4 else None
                    einnahmen.append({
                        "betrag": betrag,
                        "waehrung": "EUR",
                        "typ": f"twitch_{typ}",
                        "quelle": quelle,
                        "details": details,
                        "zeitpunkt": zeitpunkt
                    })
            # YouTube
            for row in soup.select("table.youtube-live tr")[1:]:
                cols = row.find_all("td")
                if len(cols) >= 4:
                    zeitpunkt = datetime.strptime(cols[0].text.strip(), "%d.%m.%Y %H:%M")
                    quelle = cols[1].text.strip()
                    betrag = float(cols[2].text.replace("€", "").replace(",", ".").strip())
                    typ = cols[3].text.strip().lower()
                    details = cols[4].text.strip() if len(cols) > 4 else None
                    einnahmen.append({
                        "betrag": betrag,
                        "waehrung": "EUR",
                        "typ": f"youtube_{typ}",
                        "quelle": quelle,
                        "details": details,
                        "zeitpunkt": zeitpunkt
                    })
            # In DB speichern & Telegram-Benachrichtigung bei großen Einnahmen
            inserted_count = 0
            skipped_count = 0
            for eintrag in einnahmen:
                normalized = event_from_legacy_row(eintrag)
                existing = EinnahmeInfo.query.filter_by(
                    platform=normalized["platform"],
                    username=normalized["username"],
                    captured_at=normalized["captured_at"],
                    source=normalized["source"],
                ).first()
                if existing:
                    skipped_count += 1
                    continue
                db.session.add(
                    EinnahmeInfo(
                        **eintrag,
                        platform=normalized["platform"],
                        username=normalized["username"],
                        display_name=normalized["display_name"],
                        estimated_revenue=normalized["estimated_revenue"],
                        currency=normalized["currency"],
                        captured_at=normalized["captured_at"],
                        source=normalized["source"],
                        confidence=normalized["confidence"],
                    )
                )
                inserted_count += 1
                if normalized["estimated_revenue"] >= 10:
                    msg = f"💸 Neue große Einnahme: {normalized['estimated_revenue']:.2f} EUR von {normalized['username']} ({eintrag['typ']}) am {normalized['captured_at'].strftime('%d.%m.%Y %H:%M')}\nDetails: {eintrag['details'] or '-'}"
                    send_telegram(msg)
            db.session.commit()
            logging.info(
                "%s Einnahmen gespeichert, %s Duplikate übersprungen (TikTok, Twitch, YouTube).",
                inserted_count,
                skipped_count,
            )
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
