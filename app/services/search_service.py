from ..models.profile import PublicProfile

def search_profiles(query):
    # Hier später: Echte Suche, Ranking, Provider
    # Aktuell: Demo-Query auf PublicProfile
    results = PublicProfile.query.filter(PublicProfile.username.ilike(f'%{query}%')).all()
    return results
