from functools import wraps
from flask import session, redirect, url_for, flash, abort, g
from app.models.user import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            flash('Bitte zuerst anmelden.', 'warning')
            return redirect(url_for('auth.login'))
        user = User.query.get(user_id)
        if not user or not user.is_active:
            flash('Account nicht aktiv.', 'danger')
            return redirect(url_for('auth.login'))
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user or user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(g, 'current_user', None)
            if not user or not user.has_permission(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Beispiel-Nutzung in einer Route:
# @login_required
# @role_required('admin', 'super_admin')
# def admin_dashboard(): ...
# @permission_required('manage_users')
# def manage_users(): ...
