from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from app.models.user import User
from app import db
import re

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.query.get(session['user_id'])
    return render_template('profile.html', current_user=user)

@profile_bp.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify(success=False, message='Nicht eingeloggt.')
    user = User.query.get(session['user_id'])
    data = request.get_json() or request.form
    display_name = data.get('display_name', '').strip()
    email = data.get('email', '').strip()
    bio = data.get('bio', '').strip()
    password = data.get('password', '')

    # Validierung
    if display_name and len(display_name) < 3:
        return jsonify(success=False, message='Display Name zu kurz (min. 3 Zeichen).')
    if email and (not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email)):
        return jsonify(success=False, message='Ungültige E-Mail.')
    if display_name and User.query.filter(User.display_name == display_name, User.id != user.id).first():
        return jsonify(success=False, message='Display Name existiert bereits.')
    if email and User.query.filter(User.email == email, User.id != user.id).first():
        return jsonify(success=False, message='E-Mail existiert bereits.')
    if password:
        if len(password) < 8:
            return jsonify(success=False, message='Passwort zu kurz (min. 8 Zeichen).')
        if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'\d', password):
            return jsonify(success=False, message='Passwort muss Groß-/Kleinbuchstaben und eine Zahl enthalten.')
        user.set_password(password)
    if display_name:
        user.display_name = display_name
    if email:
        user.email = email
    if bio is not None:
        user.bio = bio
    db.session.commit()
    return jsonify(success=True, message='Profil erfolgreich aktualisiert.')
