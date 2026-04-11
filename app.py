from flask import Flask, render_template, request
import os
import requests
from openai import OpenAI
from models import db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shadowseek.db')
db.init_app(app)

api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key) if api_key else None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not email or not password:
        return 'Alle Felder erforderlich!', 400
    return 'Registrierung erfolgreich!'

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return 'Alle Felder erforderlich!', 400
    return 'Login erfolgreich!'

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email', '').strip()
    if not email:
        return 'E-Mail erforderlich!', 400
    return 'Reset-Link wurde gesendet!'

@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html')

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json() or request.form
    
    # Hier die Korrektur:
    if request.is_json:
        query = data.get('query', '')
    else:
        query = data.get('username', '') or data.get('query', '')

    if not query:
        return {'error': 'Kein Suchbegriff'}, 400

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": "74c62f4b27a20f0b31df8557b403c2d18f4a7931",
        "Content-Type": "application/json"
    }
    payload = {"q": query}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=12)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {'error': str(e)}, 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))