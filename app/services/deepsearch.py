from .image_similarity import compare_uploaded_against_gallery
from .risk_score import calculate_osint_risk
from .screenshot_engine import capture_profile_screenshot
from .username_similarity import find_similar_usernames


def _safe_list(value):
    return value if isinstance(value, list) else []


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def run_deepsearch(query, profiles=None, images=None, riskdata=None):
    """
    Kombiniert mehrere Analyse-Module in eine stabile Response.
    Teilfehler bleiben lokal und brechen nicht die Gesamtantwort.
    """
    query = _safe_dict(query)
    result = {
        "similarity": {"matches": []},
        "screenshots": [],
        "image_similarity": {"matches": []},
        "risk_score": {"score": 0, "level": "low", "factors": []},
        "usernames": _safe_list(query.get("usernames")),
        "profiles": _safe_list(query.get("profiles")),
        "reverse_image": _safe_dict(query.get("reverse_image")),
    }

    if query.get("base_username") and isinstance(query.get("candidates"), list):
        try:
            result["similarity"] = {
                "matches": find_similar_usernames(
                    query["base_username"],
                    query["candidates"],
                )
            }
        except Exception:
            result["similarity"] = {"matches": []}

    screenshots = []
    for url in _safe_list(query.get("profile_urls")):
        try:
            shot = capture_profile_screenshot(url)
        except Exception:
            continue
        if shot.get("success") and shot.get("screenshot_path"):
            screenshots.append({"url": url, "path": shot["screenshot_path"]})
    result["screenshots"] = screenshots

    if query.get("reference_image") and isinstance(query.get("gallery"), list):
        try:
            image_similarity = compare_uploaded_against_gallery(
                query["reference_image"],
                query["gallery"],
            )
            if isinstance(image_similarity, dict) and isinstance(image_similarity.get("matches"), list):
                result["image_similarity"] = image_similarity
        except Exception:
            result["image_similarity"] = {"matches": []}

    risk_payload = query.get("riskdata")
    if isinstance(risk_payload, dict):
        try:
            risk_score = calculate_osint_risk(risk_payload)
            if isinstance(risk_score, dict):
                result["risk_score"] = {
                    "score": int(risk_score.get("score", 0)),
                    "level": risk_score.get("level", "low"),
                    "factors": _safe_list(risk_score.get("factors")),
                }
        except Exception:
            result["risk_score"] = {"score": 0, "level": "low", "factors": []}

    return result
