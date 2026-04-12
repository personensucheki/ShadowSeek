

from datetime import datetime
from app.input_handler import classify_url
from app.fetcher import fetch_page
from app.extractor import extract_video_data, ExtractorError
from app.normalizer import normalize
from app.logging_config import setup_logger


def process_url(url, logger, debug_dir=None):
    url_type = classify_url(url)
    result = {
        "input_url": url,
        "entity_type": url_type,
        "status": None,
        "error_code": None,
        "error_message": None,
        "scraped_at": datetime.utcnow().isoformat(),
    }
    if url_type != "video":
        result["status"] = "unsupported"
        result["error_code"] = "UNSUPPORTED_URL"
        result["error_message"] = "Nur TikTok-Video-URLs werden unterstützt."
        logger.info(f"Überspringe nicht unterstützte URL: {url}")
        return result
    fetch_result = fetch_page(url, headless=False, debug_dir=debug_dir, logger=logger)
    result["fetch_state"] = fetch_result.get("state")
    result["fetch_error"] = fetch_result.get("error")
    result["fetch_meta"] = fetch_result.get("meta")
    # Classify fetch state
    if fetch_result["state"] == "REAL_CONTENT":
        html = fetch_result["html"]
        try:
            raw_data = extract_video_data(html, debug_dir="debug", logger=logger)
            norm = normalize(raw_data)
            # Prüfe, ob mindestens video_id und author_username da sind
            if norm.get("video_id") and norm.get("author_username"):
                result.update(norm)
                result["status"] = "success"
            else:
                result.update(norm)
                result["status"] = "partial"
                result["error_code"] = "PARTIAL_DATA"
                result["error_message"] = "Nicht alle Felder konnten extrahiert werden."
        except ExtractorError as ee:
            result["status"] = "failed"
            result["error_code"] = ee.code
            result["error_message"] = ee.message
        except Exception as e:
            result["status"] = "failed"
            result["error_code"] = "EXTRACTOR_EXCEPTION"
            result["error_message"] = str(e)
    elif fetch_result["state"] == "SHELL_PAGE":
        result["status"] = "shell_page"
        result["error_code"] = "SHELL_PAGE"
        result["error_message"] = "TikTok lieferte nur Shell/Placeholder-Seite."
    elif fetch_result["state"] == "CHALLENGE_PAGE":
        result["status"] = "challenge_page"
        result["error_code"] = "CHALLENGE_PAGE"
        result["error_message"] = "TikTok lieferte Challenge/Captcha-Seite."
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
        urls (list): List of TikTok video URLs to process.
        options (dict, optional):
            debug_dir (str): Directory for debug output (optional, default None)
            logger (logging.Logger): Optional logger instance
            output_json (str): Optional path to write JSON output
            output_csv (str): Optional path to write CSV output
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
    results = []
    try:
        logger.info(f"Lade {len(urls)} URLs...")
        for url in urls:
            res = process_url(url, logger, debug_dir=debug_dir)
            results.append(res)
        logger.info(f"Fertig. Erfolgreich verarbeitet: {len([r for r in results if r['status']=='success'])} URLs.")
        # Controlled file output
        if output_json:
            try:
                from app.output import save_json, save_csv
                save_json(results, output_json)
                if output_csv:
                    save_csv(results, output_csv)
            except Exception as e:
                logger.error(f"Fehler beim Schreiben der Output-Dateien: {e}")
        return {"success": True, "data": results, "error": None}
    except Exception as e:
        logger.error(f"Scraper-Fehler: {e}")
        return {"success": False, "data": None, "error": str(e)}
