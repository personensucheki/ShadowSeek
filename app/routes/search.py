from flask import Blueprint, request, render_template
from ..services.search_service import search_profiles

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/', methods=['GET', 'POST'])
def search():
    results = []
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            results = search_profiles(query)
    return render_template('search.html', results=results)
