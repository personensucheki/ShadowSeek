import os
import re
import hashlib
from pathlib import Path

# Optional: playwright oder selenium
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

URL_REGEX = re.compile(r'^(https?://)[\w\-\.]+(\.[a-z]{2,})?(:\d+)?(/[\w\-\./?%&=]*)?$', re.IGNORECASE)


def sanitize_filename(name):
    # Entfernt Sonderzeichen, ersetzt Leerzeichen durch _
    return re.sub(r'[^a-zA-Z0-9_-]', '_', name)

def capture_profile_screenshot(url, slug=None, timeout=15):
    """
    Erstellt einen Screenshot der übergebenen URL.
    Gibt ein Dict mit Erfolg, Pfad und Fehler zurück.
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {"success": False, "message": "Playwright ist nicht installiert."}
    if not url or not URL_REGEX.match(url):
        return {"success": False, "message": "Invalid or missing URL."}
    try:
        # Dateiname erzeugen
        base = slug or hashlib.sha1(url.encode()).hexdigest()[:16]
        fname = sanitize_filename(base) + ".png"
        out_path = os.path.abspath(os.path.join(SCREENSHOT_DIR, fname))
        rel_path = f"/static/screenshots/{fname}"
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=timeout*1000)
            page.screenshot(path=out_path, full_page=True)
            browser.close()
        return {"success": True, "url": url, "screenshot_path": rel_path}
    except Exception as e:
        return {"success": False, "message": f"Screenshot failed: {e}"}
