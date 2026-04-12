
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

SCRIPT_IDS = ["SIGI_STATE", "__UNIVERSAL_DATA_FOR_REHYDRATION__", "_STATE"]

def extract_video_data(html, debug_dir=None, logger=None):

    soup = BeautifulSoup(html, "html.parser")
    script_tag = None
    for sid in SCRIPT_IDS:
        script_tag = soup.find("script", {"id": sid})
        if script_tag:
            break

    # --- BLOCK DETECTION: TikTok returns a shell page with only banners, no SIGI_STATE, no ItemModule ---
    # Heuristics: No SIGI_STATE, no __UNIVERSAL_DATA_FOR_REHYDRATION__, no _STATE, and presence of cookie banners or only meta/style tags
    if not script_tag:
        if logger:
            logger.warning("[extract_video_data] No SIGI_STATE or equivalent script found in HTML.")
        # Check for known block indicators (cookie banner, no video, only meta/style)
        banners = soup.find_all("tiktok-cookie-banner")
        meta_tags = soup.find_all("meta")
        script_tags = soup.find_all("script")
        # If there are banners and no SIGI_STATE, it's a block
        if banners or (len(meta_tags) > 10 and len(script_tags) < 3):
            if debug_dir:
                os.makedirs(debug_dir, exist_ok=True)
                with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as f:
                    f.write(html)
            raise ExtractorError("BLOCKED_OR_EMPTY", "TikTok lieferte eine leere Shell/Blockseite ohne Videodaten.")
        # Fallback: still treat as missing state script
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as f:
                f.write(html)
        raise ExtractorError("NO_STATE_SCRIPT", "Kein TikTok-State-Script gefunden.")

    try:
        data = json.loads(script_tag.string)
    except Exception as e:
        if logger:
            logger.error(f"[extract_video_data] JSON-Parsing fehlgeschlagen: {e}")
        if debug_dir:
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "debug.html"), "w", encoding="utf-8") as f:
                f.write(html)
        raise ExtractorError("INVALID_STATE_JSON", f"JSON-Parsing fehlgeschlagen: {e}")

    # ItemModule kann unterschiedlich heißen
    item_module = data.get("ItemModule") or data.get("itemModule")
    if not item_module:
        raise ExtractorError("ITEM_MODULE_MISSING", "ItemModule fehlt im TikTok-State.")

    if not isinstance(item_module, dict) or not item_module:
        raise ExtractorError("VIDEO_DATA_EMPTY", "ItemModule ist leer.")

    video_data = next(iter(item_module.values()), {})
    if not video_data:
        raise ExtractorError("VIDEO_DATA_EMPTY", "Video-Daten im ItemModule leer.")

    return {
        "video_id": video_data.get("id"),
        "description": video_data.get("desc"),
        "author_username": video_data.get("author"),
        "views": video_data.get("stats", {}).get("playCount"),
        "likes": video_data.get("stats", {}).get("diggCount"),
        "comments_count": video_data.get("stats", {}).get("commentCount"),
        "shares": video_data.get("stats", {}).get("shareCount"),
    }

class ExtractorError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
