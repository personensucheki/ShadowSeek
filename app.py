from flask import Flask, render_template, request
from models import db, Profile
import os

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
    firstname = request.args.get('firstname', '').strip()
    lastname = request.args.get('lastname', '').strip()
    city = request.args.get('city', '').strip()
    email = request.args.get('email', '').strip()

    query = Profile.query
    if username:
        query = query.filter(Profile.username.ilike(f"%{username}%"))
    if firstname:
        query = query.filter(Profile.firstname.ilike(f"%{firstname}%"))
    if lastname:
        query = query.filter(Profile.lastname.ilike(f"%{lastname}%"))
    if city:
        query = query.filter(Profile.city.ilike(f"%{city}%"))
    if email:
        query = query.filter(Profile.email.ilike(f"%{email}%"))
    results = query.all()

    return render_template('search.html', results=results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
