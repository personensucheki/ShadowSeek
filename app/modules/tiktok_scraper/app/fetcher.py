import os
import traceback
from datetime import datetime

from playwright.sync_api import sync_playwright


def fetch_page(url, headless=True, debug_dir=None, logger=None, timeout_ms=12000):
    """
    Fetch a TikTok page and classify result as:
    REAL_CONTENT, SHELL_PAGE, CHALLENGE_PAGE, BROWSER_CLOSED, FETCH_EXCEPTION.
    """
    if logger:
        logger.info("[fetch_page] start: %s", url)

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

    try:
        with sync_playwright() as playwright:
            browser = None
            context = None
            page = None
            try:
                browser = playwright.chromium.launch(headless=headless)
                user_agent = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                )
                context = browser.new_context(
                    user_agent=user_agent,
                    locale="de-DE",
                    timezone_id="Europe/Berlin",
                    viewport={"width": 1920, "height": 1080},
                    java_script_enabled=True,
                )
                page = context.new_page()
                page.set_default_timeout(timeout_ms)
                page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_timeout(1500)
                html = page.content()
                meta["user_agent"] = user_agent

                if debug_dir:
                    with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as handle:
                        handle.write(html)
                    with open(os.path.join(debug_dir, "debug_url.txt"), "w", encoding="utf-8") as handle:
                        handle.write(url)
                    with open(os.path.join(debug_dir, "debug_meta.txt"), "w", encoding="utf-8") as handle:
                        handle.write(str(meta))

                state = classify_html_state(html)
                return {"state": state, "html": html, "meta": meta, "error": None}
            except Exception as error:
                trace = traceback.format_exc()
                if logger:
                    logger.error("[fetch_page] fetch failed: %s", trace)

                try:
                    if page:
                        html = page.content()
                except Exception:
                    html = ""

                if debug_dir:
                    with open(os.path.join(debug_dir, "debug_error.txt"), "w", encoding="utf-8") as handle:
                        handle.write(str(error) + "\n" + trace)
                    if html:
                        with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as handle:
                            handle.write(html)

                return {
                    "state": "BROWSER_CLOSED" if "Browser" in str(error) else "FETCH_EXCEPTION",
                    "html": html,
                    "meta": meta,
                    "error": str(error),
                }
            finally:
                try:
                    if context:
                        context.close()
                except Exception:
                    pass
                try:
                    if browser:
                        browser.close()
                except Exception:
                    pass
    except Exception as error:
        if debug_dir:
            with open(os.path.join(debug_dir, "debug_error.txt"), "w", encoding="utf-8") as handle:
                handle.write(f"OUTER EXCEPTION: {error}\n")
        return {"state": "FETCH_EXCEPTION", "html": html, "meta": meta, "error": str(error)}


def classify_html_state(html):
    if not html or len(html) < 1000:
        return "SHELL_PAGE"

    lowered = html.lower()
    if "tiktok-verify-page" in lowered or "captcha" in lowered or "challenge" in lowered:
        return "CHALLENGE_PAGE"

    if "sigi_state" in lowered or "itemmodule" in lowered or "usermodule" in lowered:
        return "REAL_CONTENT"

    return "SHELL_PAGE"
