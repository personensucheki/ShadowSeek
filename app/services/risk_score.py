def calculate_osint_risk(data):
    """
    Berechnet einen OSINT Risk Score (0-100) und gibt Faktoren zurück.
    """
    score = 0
    factors = []
    # Punktevergabe
    if data.get('has_real_name'):
        score += 10
        factors.append('Real name detected')
    if data.get('has_location'):
        score += 15
        factors.append('Location exposed')
    if data.get('has_email'):
        score += 20
        factors.append('Email public')
    if data.get('has_phone'):
        score += 20
        factors.append('Phone number public')
    if data.get('image_reuse_score', 0) >= 80:
        score += 10
        factors.append('Profile image reused')
    if data.get('username_count', 0) >= 3:
        score += 10
        factors.append('Username reused')
    if data.get('platform_count', 0) >= 5:
        score += 10
        factors.append('Multiple platform matches')
    if data.get('has_reverse_image'):
        score += 10
        factors.append('Reverse image search hit')
    if data.get('has_age'):
        score += 5
        factors.append('Age or birth year exposed')
    # Clamp
    score = max(0, min(score, 100))
    # Level
    if score >= 75:
        level = 'critical'
    elif score >= 50:
        level = 'high'
    elif score >= 25:
        level = 'moderate'
    else:
        level = 'low'
    return {
        'score': score,
        'level': level,
        'factors': factors
    }
