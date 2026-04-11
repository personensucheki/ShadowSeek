import hashlib
import ipaddress
import re
import socket
from pathlib import Path
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


SCREENSHOT_DIR = (Path(__file__).resolve().parent.parent / "static" / "screenshots").resolve()
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_SCHEMES = {"http", "https"}
HOST_REGEX = re.compile(r"^[A-Za-z0-9.-]+$")
BLOCKED_HOSTNAMES = {"localhost"}


def sanitize_filename(name):
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", str(name or ""))
    sanitized = sanitized.strip("._")
    return sanitized[:80] or "screenshot"


def _is_blocked_ip(ip_value):
    ip_obj = ipaddress.ip_address(ip_value)
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_link_local
        or ip_obj.is_reserved
        or ip_obj.is_unspecified
        or ip_obj.is_multicast
    )


def resolve_hostname_ips(hostname):
    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return []

    addresses = []
    for info in infos:
        ip_value = info[4][0]
        if ip_value not in addresses:
            addresses.append(ip_value)
    return addresses


def is_valid_capture_url(url):
    if not isinstance(url, str) or not url.strip():
        return False, "Invalid or missing URL."

    parsed = urlparse(url.strip())
    if parsed.scheme not in ALLOWED_SCHEMES or not parsed.netloc:
        return False, "Invalid or missing URL."

    hostname = parsed.hostname
    if not hostname or not HOST_REGEX.match(hostname):
        return False, "Invalid or missing URL."

    if hostname.lower() in BLOCKED_HOSTNAMES:
        return False, "Target host is not allowed."

    addresses = resolve_hostname_ips(hostname)
    if not addresses:
        return False, "Target host could not be resolved."

    if any(_is_blocked_ip(address) for address in addresses):
        return False, "Target host is not allowed."

    return True, None


def capture_profile_screenshot(url, slug=None, timeout=15):
    """
    Erstellt einen Screenshot der angegebenen URL.
    Gibt ein Dict mit Erfolg, Pfad und Fehler zurück.
    """
    is_valid, error_message = is_valid_capture_url(url)
    if not is_valid:
        return {"success": False, "message": error_message}

    if not PLAYWRIGHT_AVAILABLE:
        return {"success": False, "message": "Playwright ist nicht installiert."}

    timeout_ms = max(1000, int(timeout * 1000))
    filename_base = sanitize_filename(slug or hashlib.sha1(url.encode("utf-8")).hexdigest()[:16])
    file_path = (SCREENSHOT_DIR / f"{filename_base}.png").resolve()

    if SCREENSHOT_DIR not in file_path.parents:
        return {"success": False, "message": "Invalid screenshot path."}

    browser = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=timeout_ms, wait_until="domcontentloaded")
            page.screenshot(path=str(file_path), full_page=True, timeout=timeout_ms)
            return {
                "success": True,
                "url": url,
                "screenshot_path": f"/static/screenshots/{file_path.name}",
            }
    except Exception as error:
        return {"success": False, "message": f"Screenshot failed: {error}"}
    finally:
        if browser is not None:
            try:
                browser.close()
            except Exception:
                pass
