from ..models.profile import PublicProfile

def get_profiles_by_username(username):
    return PublicProfile.query.filter_by(username=username).all()
