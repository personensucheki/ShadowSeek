import difflib
import re

def normalize_username(username):
    """
    Vereinheitlicht Usernamen für Vergleich.
    - Lowercase
    - Entfernt _, ., - und Whitespace
    - Trennt Zahlen ab
    """
    if not username:
        return ""
    username = username.lower()
    username = re.sub(r'[_.\-\s]', '', username)
    return username

def calculate_username_similarity(a, b):
    """
    Gibt einen Score zwischen 0 und 100 zurück.
    """
    a_norm = normalize_username(a)
    b_norm = normalize_username(b)
    ratio = difflib.SequenceMatcher(None, a_norm, b_norm).ratio()
    return int(round(ratio * 100))

def find_similar_usernames(base_username, candidates, threshold=70):
    """
    Gibt alle Kandidaten mit Score >= threshold zurück, absteigend sortiert.
    """
    results = []
    for cand in candidates:
        score = calculate_username_similarity(base_username, cand)
        if score >= threshold:
            results.append({"candidate": cand, "score": score})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results
