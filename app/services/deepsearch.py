from .username_similarity import find_similar_usernames
from .screenshot_engine import capture_profile_screenshot
from .image_similarity import compare_uploaded_against_gallery
from .risk_score import calculate_osint_risk

def run_deepsearch(query, profiles=None, images=None, riskdata=None):
    """
    Kombiniert alle Module zu einer DeepSearch-Response.
    query: dict mit 'base_username', 'candidates', 'profile_urls', 'gallery', 'riskdata' etc.
    """
    result = {}
    # Username Similarity
    if query.get('base_username') and query.get('candidates'):
        result['similarity'] = {
            'matches': find_similar_usernames(query['base_username'], query['candidates'])
        }
    else:
        result['similarity'] = {'matches': []}
    # Screenshots
    screenshots = []
    for url in query.get('profile_urls', []):
        shot = capture_profile_screenshot(url)
        if shot.get('success'):
            screenshots.append({'url': url, 'path': shot['screenshot_path']})
    result['screenshots'] = screenshots
    # Image Similarity
    if query.get('reference_image') and query.get('gallery'):
        result['image_similarity'] = compare_uploaded_against_gallery(query['reference_image'], query['gallery'])
    else:
        result['image_similarity'] = {'matches': []}
    # Risk Score
    if query.get('riskdata'):
        result['risk_score'] = calculate_osint_risk(query['riskdata'])
    else:
        result['risk_score'] = {'score': 0, 'level': 'low', 'factors': []}
    # Platzhalter für weitere Felder
    result['usernames'] = query.get('usernames', [])
    result['profiles'] = query.get('profiles', {})
    result['reverse_image'] = query.get('reverse_image', {})
    return result
