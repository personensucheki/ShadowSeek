from flask import Flask, render_template, request
from models import db, PublicProfile, User
from werkzeug.security import generate_password_hash, check_password_hash
import os
from openai import OpenAI

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
from flask import Flask, render_template, request
from models import db, PublicProfile, User
from werkzeug.security import generate_password_hash, check_password_hash
import os
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devsecret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///shadowseek.db')
db.init_app(app)

api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key) if api_key else None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods= )
def register():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not email or not password:
        return 'Alle Felder erforderlich!', 400
    return 'Registrierung erfolgreich!'

@app.route('/login', methods= )
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return 'Alle Felder erforderlich!', 400
    return 'Login erfolgreich!'

@app.route('/forgot-password', methods= )
def forgot_password():
    email = request.form.get('email', '').strip()
    if not email:
        return 'E-Mail erforderlich!', 400
    return 'Reset-Link wurde gesendet!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))from flask import Flask, render_template, request
from models import db, PublicProfile, User
from werkzeug.security import generate_password_hash, check_password_hash
import os
from openai import OpenAI

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'devsecret')
app.config = os.environ.get('DATABASE_URL', 'sqlite:///shadowseek.db')
db.init_app(app)

api_key = os.environ.get('OPENAI_API_KEY')
client = OpenAI(api_key=api_key) if api_key else None

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods= )
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

@app.route('/forgot-password', methods= )
def forgot_password():
    email = request.form.get('email', '').strip()
    if not email:
        return 'E-Mail erforderlich!', 400
    return 'Reset-Link wurde gesendet!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))