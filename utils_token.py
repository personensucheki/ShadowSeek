from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_reset_token(user_id, expires_sec=3600):
    s = URLSafeTimedSerializer(current_app.secret_key)
    return s.dumps({'user_id': user_id})

def verify_reset_token(token, max_age=3600):
    s = URLSafeTimedSerializer(current_app.secret_key)
    try:
        data = s.loads(token, max_age=max_age)
        return data['user_id']
    except Exception:
        return None
