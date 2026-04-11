
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import os, re
from models import db, User
from werkzeug.security import generate_password_hash

# Flask-App-Instanz ganz oben definieren
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shadowseek.db')
db.init_app(app)

# API-Route erst nach app-Definition
@app.route('/api/chatbot', methods=['POST'])
def api_chatbot():
    data = request.get_json() or request.form
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'error': 'Keine Nachricht erhalten.'}), 400
    # Demo-Response
    bot_reply = f"Demo: Du hast gesagt: {user_message}"
    return jsonify({'reply': bot_reply})

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        # Validierung
        if not username or not email or not password:
            return 'Alle Felder erforderlich!', 400
        if not re.match(r"^[\w.-]{3,32}$", username):
            return 'Ungültiger Benutzername (3-32 Zeichen, Buchstaben/Zahlen/._- erlaubt)', 400
        if not re.match(r"^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$", email):
            return 'Ungültige E-Mail-Adresse!', 400
        if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            return 'Passwort zu schwach (mind. 8 Zeichen, Buchstaben & Zahl)', 400
        # Existenz prüfen
        if User.query.filter_by(username=username).first():
            return 'Benutzername bereits vergeben!', 400
        if User.query.filter_by(email=email).first():
            return 'E-Mail bereits registriert!', 400
        # Passwort hashen
        pw_hash = generate_password_hash(password)
        user = User(username=username, email=email, password_hash=pw_hash)
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return 'Fehler beim Speichern. Bitte versuche es erneut.', 500
        # Session-Start
        session['user_id'] = user.id
        session['username'] = user.username
        return redirect(url_for('home'))
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return 'Alle Felder erforderlich!', 400
    return 'Login erfolgreich!'

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    email = request.form.get('email', '').strip()
    if not email:
        return 'E-Mail erforderlich!', 400
    return 'Reset-Link wurde gesendet!'

@app.route('/search', methods=['GET', 'POST'])
def search():
    return render_template('search.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json() or request.form
    query = data.get('query') or data.get('username', '').strip()
    
    if not query:
        return {'error': 'Kein Suchbegriff'}, 400

    # Struktur, die dein JavaScript genau erwartet
    return {
        "categorized_results": {
            "Social Media": [
                {"username": query, "platform": "Instagram", "match_score": 95, "profile_url": f"https://instagram.com/{query}"},
                {"username": query + ".official", "platform": "TikTok", "match_score": 88, "profile_url": "#"},
                {"username": query, "platform": "Twitter", "match_score": 76, "profile_url": "#"},
                {"username": query, "platform": "Tinder", "match_score": 91, "profile_url": "#"},
                {"username": query, "platform": "Bumble", "match_score": 84, "profile_url": "#"},
                {"username": query, "platform": "OnlyFans", "match_score": 93, "profile_url": "#"},
                {"username": query + "x", "platform": "Pornhub", "match_score": 79, "profile_url": "#"}
            ]
        }
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))