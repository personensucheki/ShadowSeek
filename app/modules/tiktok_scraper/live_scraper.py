
import csv
import re
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

LIVE_URL = "https://www.tiktok.com/live"
SOURCE_NAME = "tiktok_live"
SCROLL_STEPS = 7
SCROLL_DELAY_SECONDS = 2
PAGE_LOAD_TIMEOUT_MS = 45000
PROFILE_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9._-]+(?:[/?#][^\s\"'>]*)?",
    re.IGNORECASE,
)


def normalize_profile_url(raw_url):
    if not raw_url:
        return None

    url = raw_url.strip()
    if url.startswith("//"):
        url = f"https:{url}"
    elif url.startswith("/@"):
        url = f"https://www.tiktok.com{url}"

    if not re.match(r"^https?://", url, re.IGNORECASE):
        return None

    parsed = urlparse(url)
    if "tiktok.com" not in parsed.netloc.lower():
        return None

    match = re.match(r"^/@([A-Za-z0-9._-]+)", parsed.path)
    if not match:
        return None

    username = match.group(1)
    return f"https://www.tiktok.com/@{username}"


def extract_profile_urls_from_hrefs(hrefs):
    normalized_urls = []
    seen = set()

    for href in hrefs:
        candidates = PROFILE_URL_PATTERN.findall(href) if href else []

        if not candidates and href:
            candidates = [href]

        for candidate in candidates:
            normalized = normalize_profile_url(candidate)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            normalized_urls.append(normalized)

    return normalized_urls


def collect_hrefs(page):
    return page.eval_on_selector_all(
        "a[href]",
        "elements => elements.map(element => element.href || element.getAttribute('href') || '')",
    )


def scroll_page(page, steps=SCROLL_STEPS, delay_seconds=SCROLL_DELAY_SECONDS):
    for _ in range(steps):
        page.mouse.wheel(0, 1800)
        page.wait_for_timeout(delay_seconds * 1000)


def export_profiles(profile_urls, output_path):
    with open(output_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["profile_url", "source"])
        writer.writeheader()
        for profile_url in profile_urls:
            writer.writerow({"profile_url": profile_url, "source": SOURCE_NAME})



# Internal entrypoint for ShadowSeek
def run_live_profile_scraper(options=None):
    """
    Scrape TikTok live profile URLs.
    Args:
        options (dict, optional):
            output_csv (str): Optional path to write CSV output
            logger (logging.Logger): Optional logger instance
    Returns:
        dict: {
            "success": bool,
            "data": list of profile URLs or None,
            "error": error message or None
        }
    """
    if options is None:
        options = {}
    output_csv = options.get("output_csv")
    logger = options.get("logger")
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(PAGE_LOAD_TIMEOUT_MS)
            page.goto(LIVE_URL, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except PlaywrightTimeoutError:
                pass
            try:
                page.wait_for_selector("a[href*='tiktok.com/@'], a[href^='/@']", timeout=15000)
            except PlaywrightTimeoutError:
                page.wait_for_timeout(5000)
            page.wait_for_timeout(3000)

            scroll_page(page)
            hrefs = collect_hrefs(page)
            browser.close()

        raw_link_count = len(hrefs)
        normalized_urls = extract_profile_urls_from_hrefs(hrefs)

        if output_csv:
            try:
                export_profiles(normalized_urls, output_csv)
            except Exception as e:
                if logger:
                    logger.error(f"Fehler beim Schreiben der Output-Datei: {e}")
        return {"success": True, "data": normalized_urls, "error": None}
    except Exception as e:
        if logger:
            logger.error(f"Live scraper Fehler: {e}")
        return {"success": False, "data": None, "error": str(e)}
