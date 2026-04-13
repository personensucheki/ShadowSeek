from datetime import datetime

from .extractor import ExtractorError, extract_profile_data, extract_video_data
from .fetcher import fetch_page
from .input_handler import classify_url
from .logging_config import setup_logger
from .normalizer import normalize


def process_url(url, logger, debug_dir=None, headless=True, timeout_ms=12000):
    url_type = classify_url(url)
    result = {
        "input_url": url,
        "entity_type": url_type,
        "status": None,
        "error_code": None,
        "error_message": None,
        "scraped_at": datetime.utcnow().isoformat(),
    }

    if url_type not in {"video", "profile"}:
        result["status"] = "unsupported"
        result["error_code"] = "UNSUPPORTED_URL"
        result["error_message"] = "Nur TikTok-Profil- oder Video-URLs werden unterstuetzt."
        logger.info("Ueberspringe nicht unterstuetzte URL: %s", url)
        return result

    fetch_result = fetch_page(
        url,
        headless=headless,
        debug_dir=debug_dir,
        logger=logger,
        timeout_ms=timeout_ms,
    )
    result["fetch_state"] = fetch_result.get("state")
    result["fetch_error"] = fetch_result.get("error")
    result["fetch_meta"] = fetch_result.get("meta")

    if fetch_result["state"] == "REAL_CONTENT":
        html = fetch_result["html"]
        try:
            if url_type == "video":
                raw_data = extract_video_data(html, debug_dir=debug_dir, logger=logger)
                norm = normalize(raw_data)
                result.update(norm)
                if norm.get("video_id") and norm.get("author_username"):
                    result["status"] = "success"
                else:
                    result["status"] = "partial"
                    result["error_code"] = "PARTIAL_DATA"
                    result["error_message"] = "Nicht alle Felder konnten extrahiert werden."
            else:
                profile_data = extract_profile_data(html, debug_dir=debug_dir, logger=logger)
                result.update(profile_data)
                if result.get("author_username"):
                    result["status"] = "success"
                else:
                    result["status"] = "partial"
                    result["error_code"] = "PARTIAL_DATA"
                    result["error_message"] = "Profil geladen, aber Username konnte nicht extrahiert werden."
        except ExtractorError as error:
            result["status"] = "failed"
            result["error_code"] = error.code
            result["error_message"] = error.message
        except Exception as error:  # pragma: no cover
            result["status"] = "failed"
            result["error_code"] = "EXTRACTOR_EXCEPTION"
            result["error_message"] = str(error)
    elif fetch_result["state"] == "SHELL_PAGE":
        result["status"] = "shell_page"
        result["error_code"] = "SHELL_PAGE"
        result["error_message"] = "TikTok lieferte nur eine Shell/Placeholder-Seite."
    elif fetch_result["state"] == "CHALLENGE_PAGE":
        result["status"] = "challenge_page"
        result["error_code"] = "CHALLENGE_PAGE"
        result["error_message"] = "TikTok lieferte eine Challenge/Captcha-Seite."
    elif fetch_result["state"] == "BROWSER_CLOSED":
        result["status"] = "browser_closed"
        result["error_code"] = "BROWSER_CLOSED"
        result["error_message"] = fetch_result.get("error") or "Browser wurde unerwartet geschlossen."
    elif fetch_result["state"] == "FETCH_EXCEPTION":
        result["status"] = "fetch_failed"
        result["error_code"] = "FETCH_EXCEPTION"
        result["error_message"] = fetch_result.get("error") or "Unbekannter Fetch-Fehler."
    else:
        result["status"] = "unknown"
        result["error_code"] = "UNKNOWN_FETCH_STATE"
        result["error_message"] = f"Unbekannter Fetch-State: {fetch_result.get('state')}"

    return result


# Internal entrypoint for ShadowSeek
def run_scraper(urls, options=None):
    """
    Main entrypoint for TikTok scraper module.
    Args:
        urls (list): List of TikTok profile or video URLs to process.
        options (dict, optional):
            debug_dir (str): Directory for debug output (optional, default None)
            logger (logging.Logger): Optional logger instance
            output_json (str): Optional path to write JSON output
            output_csv (str): Optional path to write CSV output
            headless (bool): Run browser in headless mode (default True)
    Returns:
        dict: {
            "success": bool,
            "data": list of results or None,
            "error": error message or None
        }
    """
    if options is None:
        options = {}

    debug_dir = options.get("debug_dir")
    logger = options.get("logger") or setup_logger()
    output_json = options.get("output_json")
    output_csv = options.get("output_csv")
    headless = options.get("headless", True)
    timeout_ms = int(options.get("timeout_ms", 12000))
    results = []

    try:
        logger.info("Lade %s URLs...", len(urls))
        for url in urls:
            results.append(
                process_url(
                    url,
                    logger,
                    debug_dir=debug_dir,
                    headless=headless,
                    timeout_ms=timeout_ms,
                )
            )

        logger.info(
            "Fertig. Erfolgreich verarbeitet: %s URLs.",
            len([entry for entry in results if entry["status"] == "success"]),
        )

        if output_json:
            try:
                from .output import save_csv, save_json

                save_json(results, output_json)
                if output_csv:
                    save_csv(results, output_csv)
            except Exception as error:  # pragma: no cover
                logger.error("Fehler beim Schreiben der Output-Dateien: %s", error)

        return {"success": True, "data": results, "error": None}
    except Exception as error:
        logger.error("Scraper-Fehler: %s", error)
        return {"success": False, "data": None, "error": str(error)}
