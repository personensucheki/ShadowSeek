from flask import Blueprint, request, jsonify
from app.services.screenshot_engine import capture_profile_screenshot
from app.services.username_similarity import find_similar_usernames
from app.services.image_similarity import compare_uploaded_against_gallery
from app.services.risk_score import calculate_osint_risk
from app.services.deepsearch import run_deepsearch

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/search/screenshot', methods=['POST'])
def screenshot():
    data = request.get_json() or {}
    url = data.get('url')
    slug = data.get('slug')
    result = capture_profile_screenshot(url, slug)
    if result.get('success'):
        return jsonify(success=True, data=result)
    return jsonify(success=False, message=result.get('message', 'Screenshot failed')), 400

@analysis_bp.route('/search/similarity', methods=['POST'])
def similarity():
    data = request.get_json() or {}
    base = data.get('base_username')
    candidates = data.get('candidates', [])
    if not base or not candidates:
        return jsonify(success=False, message='Missing base_username or candidates'), 400
    matches = find_similar_usernames(base, candidates)
    return jsonify(success=True, data={'matches': matches})

@analysis_bp.route('/search/image-similarity', methods=['POST'])
def image_similarity():
    data = request.get_json() or {}
    ref = data.get('reference_image')
    gallery = data.get('gallery', [])
    if not ref or not gallery:
        return jsonify(success=False, message='Missing reference_image or gallery'), 400
    result = compare_uploaded_against_gallery(ref, gallery)
    return jsonify(success=True, data=result)

@analysis_bp.route('/search/risk-score', methods=['POST'])
def risk_score():
    data = request.get_json() or {}
    result = calculate_osint_risk(data)
    return jsonify(success=True, data=result)

@analysis_bp.route('/search/deepsearch', methods=['POST'])
def deepsearch():
    data = request.get_json() or {}
    result = run_deepsearch(data)
    return jsonify(success=True, data=result)
