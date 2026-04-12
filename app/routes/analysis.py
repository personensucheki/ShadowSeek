from flask import Blueprint, jsonify, request
from app.services.response_utils import api_success, api_error

from app.services.deepsearch import run_deepsearch
from app.services.image_similarity import compare_uploaded_against_gallery
from app.services.risk_score import calculate_osint_risk
from app.services.screenshot_engine import capture_profile_screenshot
from app.services.username_similarity import find_similar_usernames


analysis_bp = Blueprint("analysis", __name__)



def _json_error(message, status_code=400, errors=None):
    return api_error(message, status=status_code, errors=errors)


def _get_json_payload():
    if not request.is_json:
        return None, _json_error("JSON body required.", 400)

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, _json_error("Invalid JSON body.", 400)

    return data, None


@analysis_bp.route("/search/screenshot", methods=["POST"])
def screenshot():
    data, error = _get_json_payload()
    if error:
        return error

    url = (data.get("url") or "").strip()
    slug = data.get("slug")
    if not url:
        return _json_error("Missing url.", 400)

    result = capture_profile_screenshot(url, slug)
    if result.get("success"):
        return api_success(data=result)
    return api_error(result.get("message", "Screenshot failed."), status=400)


@analysis_bp.route("/search/similarity", methods=["POST"])
def similarity():
    data, error = _get_json_payload()
    if error:
        return error

    base = (data.get("base_username") or "").strip()
    candidates = data.get("candidates")
    if not base or not isinstance(candidates, list) or not candidates:
        return _json_error("Missing base_username or candidates.", 400)

    matches = find_similar_usernames(base, candidates)
    return api_success(data={"matches": matches})


@analysis_bp.route("/search/image-similarity", methods=["POST"])
def image_similarity():
    data, error = _get_json_payload()
    if error:
        return error

    reference_image = data.get("reference_image")
    gallery = data.get("gallery")
    if not reference_image or not isinstance(gallery, list) or not gallery:
        return _json_error("Missing reference_image or gallery.", 400)

    result = compare_uploaded_against_gallery(reference_image, gallery)
    return jsonify(success=True, data=result), 200


@analysis_bp.route("/search/risk-score", methods=["POST"])
def risk_score():
    data, error = _get_json_payload()
    if error:
        return error

    result = calculate_osint_risk(data)
    return jsonify(success=True, data=result), 200


@analysis_bp.route("/search/deepsearch", methods=["POST"])
def deepsearch():
    data, error = _get_json_payload()
    if error:
        return error

    result = run_deepsearch(data)
    return jsonify(success=True, data=result), 200
