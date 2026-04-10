from flask import Flask, render_template, request
from models import db, PublicProfile
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
from openai import OpenAI

app = Flask(__name__)
app.config['DEBUG'] = True
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# --- ShadowSeek Search Algorithmus v1.0 (Flask-kompatibel) ---
def shadowseek_search(query):
    def generate_profile_url(platform, username):
        urls = {
            'Instagram': f'https://instagram.com/{username}',
            'TikTok': f'https://tiktok.com/@{username}',
            'Twitter/X': f'https://twitter.com/{username}',
            'Facebook': f'https://facebook.com/{username}',
            'Reddit': f'https://reddit.com/user/{username}',
            'OnlyFans': f'https://onlyfans.com/{username}',
            'Fansly': f'https://fansly.com/{username}',
            'Pornhub': f'https://pornhub.com/users/{username}',
            'ManyVids': f'https://manyvids.com/Profile/{username}',
            'Stripchat': f'https://stripchat.com/{username}',
        }
        return urls.get(platform, '#')

    username = query.get('username', '').strip()
    if not username:
        return None

    def shadowseek_search(query):
        username = query.get('username', '').strip()
        firstname = query.get('firstname', '').strip()
        lastname = query.get('lastname', '').strip()
        city = query.get('city', '').strip()
        email = query.get('email', '').strip()

        # Mindestens ein Feld muss ausgefüllt sein
        if not (username or firstname or lastname or city or email):
            return None

        # Username hat höchste Priorität, aber auch andere Felder reichen aus
        search_term = username or firstname or lastname or email or city

        score = 65
        if username: score += 25
        if firstname: score += 12
        if lastname: score += 15
        if city: score += 8
        if email: score += 18

        platforms = {
            'social': [('Instagram', 92), ('TikTok', 87), ('Twitter/X', 79), ('Facebook', 71)],
            'dating': [('OnlyFans', 91), ('Fansly', 83)],
            'porn': [('Pornhub', 91), ('ManyVids', 83), ('Stripchat', 76)]
        }

        categorized_results = {}
        for category, plat_list in platforms.items():
            categorized_results[category] = []
            for name, base_score in plat_list:
                final_score = min(99, int(base_score + (score - 65) * 0.8))
                profile = {
                    'username': search_term,
                    'platform': name,
                    'profile_url': f"https://{name.lower().replace('/', '').replace(' ', '')}.com/{search_term.lower()}",
                    'match_score': final_score,
                    'category': category
                }
                categorized_results[category].append(profile)

        return {
            'categorized_results': categorized_results,
            'meta': {
                'query': search_term,
                'total_profiles': sum(len(v) for v in categorized_results.values()),
                'agent_confidence': min(98, score + 15),
                'search_depth': 'Deep Scan' if score > 85 else 'Standard Scan'
            }
        }
    db.create_all()

# Chatbot-API-Route (direkt vor /search)
@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')

    if not user_message:
        return {'error': 'No message'}, 400

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Du bist ShadowSeek Assistant. Ein cooler, direkter und etwas frecher KI-Assistent für eine Personensuchmaschine. Du hilfst bei Fragen zu Social Media Profilen, Datenschutz und Deep Search. Antworte kurz, frech und auf Deutsch."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=300,
            temperature=0.7
        )
        return {'reply': response.choices[0].message.content}
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/search', methods=['POST'])
def api_search():
    data = request.get_json()
    query = data.get('query', '')
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        return {'error': 'Serper API-Key fehlt'}, 500
    if not query:
        return {'error': 'Kein Suchbegriff angegeben'}, 400

    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": query}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/')
def home():
    return render_template('home.html')






@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        city = request.form.get('city', '').strip()
        email = request.form.get('email', '').strip()
    else:
        username = request.args.get('username', '').strip()
        firstname = request.args.get('firstname', '').strip()
        lastname = request.args.get('lastname', '').strip()
        city = request.args.get('city', '').strip()
        email = request.args.get('email', '').strip()

    query_data = {
        'username': username,
        'firstname': firstname,
        'lastname': lastname,
        'city': city,
        'email': email
    }

    results = shadowseek_search(query_data)

    return render_template('search.html', 
                           categorized_results=results if results else {},
                           meta=results if results else {},
                           username=username,
                           firstname=firstname,
                           lastname=lastname,
                           city=city,
                           email=email)


# --- User Model (if not present in models.py) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

# --- Auth Routes for Modal Forms ---
from flask import redirect, url_for, flash

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        return "Username existiert bereits", 400
    if User.query.filter_by(email=email).first():
        return "E-Mail existiert bereits", 400

    new_user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password)
    )
    db.session.add(new_user)
    db.session.commit()
    return "Registrierung erfolgreich!"

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return "Login erfolgreich!"
    return "Falscher Username oder Passwort", 401

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email')
    # Hier später echte E-Mail-Funktion einbauen
    return "Wenn die E-Mail existiert, wurde ein Reset-Link gesendet."



# Neue Route zum Einfügen von 12 Testdaten
@app.route('/add_testdata')
def add_testdata():
    test_profiles = [
        # Social Media
        PublicProfile(
            username='julia.smith', platform='Instagram', category='social',
            profile_url='https://instagram.com/julia.smith',
            profile_pic='https://randomuser.me/api/portraits/women/44.jpg',
            bio='Travel | Fashion | Coffee',
        ),
        PublicProfile(
            username='danceking99', platform='TikTok', category='social',
            profile_url='https://tiktok.com/@danceking99',
            profile_pic='https://randomuser.me/api/portraits/men/32.jpg',
            bio='Dancer & Entertainer',
        ),
        PublicProfile(
            username='realmax', platform='Twitter', category='social',
            profile_url='https://twitter.com/realmax',
            profile_pic='https://randomuser.me/api/portraits/men/12.jpg',
            bio='Tech enthusiast. Opinions my own.',
        ),
        PublicProfile(
            username='laura.fb', platform='Facebook', category='social',
            profile_url='https://facebook.com/laura.fb',
            profile_pic='https://randomuser.me/api/portraits/women/25.jpg',
            bio='Marketing | Social Media',
        ),
        # Dating/Adult
        PublicProfile(
            username='naughty_nina', platform='OnlyFans', category='adult',
            profile_url='https://onlyfans.com/naughty_nina',
            profile_pic='https://randomuser.me/api/portraits/women/21.jpg',
            bio='Exclusive content',
        ),
        PublicProfile(
            username='fansly_guy', platform='Fansly', category='adult',
            profile_url='https://fansly.com/fansly_guy',
            profile_pic='https://randomuser.me/api/portraits/men/41.jpg',
            bio='DMs open for requests',
        ),
        PublicProfile(
            username='lisa_heart', platform='Tinder', category='dating',
            profile_url='https://tinder.com/@lisa_heart',
            profile_pic='https://randomuser.me/api/portraits/women/65.jpg',
            bio='Looking for real connections',
        ),
        # Porn
        PublicProfile(
            username='hotstarxxx', platform='Pornhub', category='porn',
            profile_url='https://pornhub.com/users/hotstarxxx',
            profile_pic='https://randomuser.me/api/portraits/men/55.jpg',
            bio='Verified amateur',
        ),
        PublicProfile(
            username='vidqueen', platform='ManyVids', category='porn',
            profile_url='https://manyvids.com/Profile/vidqueen',
            profile_pic='https://randomuser.me/api/portraits/women/77.jpg',
            bio='MV Star | Custom Videos',
        ),
        PublicProfile(
            username='stripstar', platform='Stripchat', category='porn',
            profile_url='https://stripchat.com/stripstar',
            profile_pic='https://randomuser.me/api/portraits/men/88.jpg',
            bio='Live cam every night',
        ),
        # Extra adult
        PublicProfile(
            username='mature_mia', platform='OnlyFans', category='adult',
            profile_url='https://onlyfans.com/mature_mia',
            profile_pic='https://randomuser.me/api/portraits/women/54.jpg',
            bio='Mature content 18+',
        ),
        # Extra porn
        PublicProfile(
            username='darkdesire', platform='Pornhub', category='porn',
            profile_url='https://pornhub.com/users/darkdesire',
            profile_pic='https://randomuser.me/api/portraits/men/99.jpg',
            bio='Verified couple',
        ),
    ]
    with app.app_context():
        db.session.bulk_save_objects(test_profiles)
        db.session.commit()
    return f"{len(test_profiles)} Testprofile wurden erfolgreich eingefügt!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
