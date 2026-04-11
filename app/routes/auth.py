from flask import Blueprint, request, render_template, redirect, url_for, flash, session

from ..models.user import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        if not username or not email or not password:
            flash('Alle Felder erforderlich!', 'danger')
            return render_template('register.html')
        if User.query.filter_by(username=username).first():
            flash('Username existiert bereits!', 'danger')
            return render_template('register.html')
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registrierung erfolgreich! Bitte einloggen.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Ungültige Zugangsdaten!', 'danger')
            return render_template('login.html')
        session['user_id'] = user.id
        flash('Login erfolgreich!', 'success')
        return redirect(url_for('search.search'))
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Abgemeldet.', 'info')
    return redirect(url_for('auth.login'))
