from flask import Flask, render_template, request
from models import db, PublicProfile
import os
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shadowseek.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/search')
def search():
    username = request.args.get('username', '').strip()
    # Optional: Kategorie-Filter aus Query-Param
    category = request.args.get('category', '').strip().lower()

    # Suche nach Username (und optional Kategorie)
    query = PublicProfile.query
    if username:
        query = query.filter(PublicProfile.username.ilike(f"%{username}%"))
    results = query.all()

    # Ergebnisse nach Kategorie sortieren
    categories = ['social', 'dating', 'adult', 'porn']
    categorized_results = {cat: [] for cat in categories}
    for profile in results:
        cat = (profile.category or '').lower()
        if cat in categorized_results:
            categorized_results[cat].append(profile)

    return render_template('search.html', results=results, categorized_results=categorized_results)



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
