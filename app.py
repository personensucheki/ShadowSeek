from flask import Flask, render_template, request
import os
from models import db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shadowseek.db')
db.init_app(app)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not email or not password:
        return 'Alle Felder erforderlich!', 400
    return 'Registrierung erfolgreich!'

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