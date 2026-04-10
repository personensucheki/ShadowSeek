

from flask import Flask, render_template, request
from models import db, PublicProfile
import os
import requests
from openai import OpenAI

app = Flask(__name__)
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

    # 1. Basis-Score berechnen
    score = 65

    # 2. Bonus für zusätzliche Infos
    if query.get('firstname'): score += 12
    if query.get('lastname'): score += 15
    if query.get('city'): score += 8
    if query.get('email'): score += 18

    # 3. Plattformen & Kategorien
    platforms = {
        'social': [
            ('Instagram', 92),
            ('TikTok', 87),
            ('Twitter/X', 79),
            ('Facebook', 71),
            ('Reddit', 64)
        ],
        'dating': [
            ('OnlyFans', 91),
            ('Fansly', 83)
        ],
        'porn': [
            ('Pornhub', 91),
            ('ManyVids', 83),
            ('Stripchat', 76)
        ]
    }

    categorized_results = {}
    for category, plat_list in platforms.items():
        categorized_results[category] = []
        for name, base_score in plat_list:
            final_score = min(99, int(base_score + (score - 65) * 0.8))
            profile = {
                'username': username,
                'platform': name,
                'profile_url': generate_profile_url(name, username),
                'match_score': final_score,
                'category': category
            }
            categorized_results[category].append(profile)

    total_findings = sum(len(profiles) for profiles in categorized_results.values())

    return {
        'categorized_results': categorized_results,
        'meta': {
            'query': username,
            'total_profiles': total_findings,
            'agent_confidence': min(98, score + 15),
            'search_depth': 'Deep Scan' if score > 85 else 'Standard Scan',
            'timestamp': 'just now'
        }
    }

# --- Agenten-Style Loading-Text-Liste (deutsch) ---
SHADOWSEEK_LOADING_TEXTS = [
    "Initialisiere ShadowSeek Agent...",
    "Lade neuronale Suchmatrix...",
    "Durchsuche Social Media Netzwerke...",
    "Scanne Dating & Adult Plattformen...",
    "Analysiere Deep-Web Verbindungen...",
    "Kombiniere Metadaten & Querverweise...",
    "Berechne Match-Scores...",
    "Finalisiere Agenten-Report...",
    "Erstelle Ergebnisübersicht...",
    "Suche abgeschlossen – Ergebnisse werden geladen..."
]


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shadowseek.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
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

@app.route('/')
def home():
    return render_template('home.html')




@app.route('/search')
def search():
    username = request.args.get('username', '').strip()
    firstname = request.args.get('firstname', '').strip()
    lastname = request.args.get('lastname', '').strip()
    
    categorized_results = {
        'social': []
    }

    if username:
        platforms = [
            {'name': 'Instagram', 'url': f'https://instagram.com/{username}', 'category': 'social'},
            {'name': 'TikTok', 'url': f'https://tiktok.com/@{username}', 'category': 'social'},
            {'name': 'Twitter/X', 'url': f'https://twitter.com/{username}', 'category': 'social'},
            {'name': 'Facebook', 'url': f'https://facebook.com/{username}', 'category': 'social'},
            {'name': 'OnlyFans', 'url': f'https://onlyfans.com/{username}', 'category': 'adult'},
            {'name': 'Fansly', 'url': f'https://fansly.com/{username}', 'category': 'adult'},
            {'name': 'Pornhub', 'url': f'https://pornhub.com/users/{username}', 'category': 'porn'},
            {'name': 'ManyVids', 'url': f'https://manyvids.com/Profile/{username}', 'category': 'porn'},
            {'name': 'Stripchat', 'url': f'https://stripchat.com/{username}', 'category': 'porn'},
        ]

        for p in platforms:
            profile = {
                'username': username,
                'platform': p['name'],
                'profile_url': p['url'],
                'match_score': 85 if p['category'] == 'social' else 78
            }
            if p['category'] == 'social':
                categorized_results['social'].append(profile)

    return render_template('search.html', 
                           categorized_results=categorized_results, 
                           username=username)



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
