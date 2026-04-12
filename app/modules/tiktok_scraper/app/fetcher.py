
from playwright.sync_api import sync_playwright
import os
from datetime import datetime
import traceback

def fetch_page(url, headless=True, debug_dir=None, logger=None):
    """
    Fetches a TikTok page and classifies the result into one of:
    REAL_CONTENT, SHELL_PAGE, CHALLENGE_PAGE, BROWSER_CLOSED, FETCH_EXCEPTION
    Returns a dict with keys: state, html, meta, error (if any)
    """
    import random
    if logger:
        logger.info(f"[fetch_page] START FETCH for url: {url}")
    if debug_dir:
        os.makedirs(debug_dir, exist_ok=True)
    html = ""
    meta = {
        "url": url,
        "headless": headless,
        "datetime": datetime.now().isoformat(),
        "user_agent": None,
        "locale": "de-DE",
        "timezone_id": "Europe/Berlin",
        "viewport": {"width": 1920, "height": 1080},
    }
    error = None
    state = None
    try:
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=headless)
            except Exception as e:
                state = "BROWSER_CLOSED"
                error = str(e)
                html = ""
                if logger:
                    logger.error(f"[fetch_page] BROWSER LAUNCH FAILED: {e}")
                if debug_dir:
                    with open(os.path.join(debug_dir, "debug_error.txt"), "w", encoding="utf-8") as f:
                        f.write(f"BROWSER LAUNCH FAILED: {e}\n")
                return {"state": state, "html": html, "meta": meta, "error": error}

            try:
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                    locale="de-DE",
                    timezone_id="Europe/Berlin",
                    viewport={"width": 1920, "height": 1080},
                    java_script_enabled=True,
                )
                page = context.new_page()
                # Human-like delay before navigation
                page.wait_for_timeout(random.randint(200, 600))
                page.goto(url, timeout=60000)
                # Wait for network idle or a bit longer
                page.wait_for_timeout(random.randint(3500, 6000))
                # Optional: small scroll to trigger lazy load
                try:
                    page.mouse.wheel(0, random.randint(100, 400))
                    page.wait_for_timeout(random.randint(200, 600))
                except Exception:
                    pass
                try:
                    html = page.content()
                    if logger:
                        logger.info(f"[fetch_page] HTML CAPTURED for url: {url}")
                except Exception as e:
                    html = ""
                    if logger:
                        logger.warning(f"[fetch_page] HTML CAPTURE FAILED for url: {url}")
                meta["user_agent"] = page.context.user_agent
                # Write debug files
                if debug_dir:
                    with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as f:
                        f.write(html)
                    with open(os.path.join(debug_dir, "debug_url.txt"), "w", encoding="utf-8") as f:
                        f.write(url)
                    with open(os.path.join(debug_dir, "debug_meta.txt"), "w", encoding="utf-8") as f:
                        f.write(str(meta))
                # Classify page
                state = classify_html_state(html)
                return {"state": state, "html": html, "meta": meta, "error": None}
            except Exception as e:
                error = str(e)
                tb = traceback.format_exc()
                if logger:
                    logger.error(f"[fetch_page] FETCH ERROR: {tb}")
                state = "FETCH_EXCEPTION"
                if debug_dir:
                    with open(os.path.join(debug_dir, "debug_error.txt"), "w", encoding="utf-8") as f:
                        f.write(str(e) + "\n" + tb)
                # Try to dump HTML if possible
                try:
                    html = page.content()
                    if debug_dir:
                        with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as f:
                            f.write(html)
                except Exception:
                    pass
                return {"state": state, "html": html, "meta": meta, "error": error}
            finally:
                if logger:
                    logger.info(f"[fetch_page] BROWSER CLOSED for url: {url}")
                try:
                    browser.close()
                except Exception:
                    pass
    except Exception as e:
        state = "FETCH_EXCEPTION"
        error = str(e)
        if debug_dir:
            with open(os.path.join(debug_dir, "debug_error.txt"), "w", encoding="utf-8") as f:
                f.write(f"OUTER EXCEPTION: {e}\n")
        return {"state": state, "html": html, "meta": meta, "error": error}


def classify_html_state(html):
    """
    Classifies the HTML into one of:
    REAL_CONTENT, SHELL_PAGE, CHALLENGE_PAGE
    """
    if not html or len(html) < 1000:
        return "SHELL_PAGE"
    # TikTok challenge/captcha pages often have recognizable markers
    if "tiktok-verify-page" in html or "captcha" in html or "challenge" in html:
        return "CHALLENGE_PAGE"
    # Real content: look for SIGI_STATE or ItemModule
    if "SIGI_STATE" in html or "ItemModule" in html:
        return "REAL_CONTENT"
    # Fallback: shell
    return "SHELL_PAGE"
