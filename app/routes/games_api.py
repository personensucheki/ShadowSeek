import requests
from flask import Blueprint, request, jsonify

games_api_bp = Blueprint("games_api", __name__)

# RAWG API Key (optional, falls vorhanden)
RAWG_API_KEY = None  # Trage hier deinen Key ein
RAWG_BASE_URL = "https://api.rawg.io/api/games"

# Lokale Fallback-Liste
FALLBACK_GAMES = [
    {"id": "valorant", "name": "Valorant", "cover": ""},
    {"id": "fortnite", "name": "Fortnite", "cover": ""},
    {"id": "minecraft", "name": "Minecraft", "cover": ""},
    {"id": "league-of-legends", "name": "League of Legends", "cover": ""},
    {"id": "apex-legends", "name": "Apex Legends", "cover": ""},
    {"id": "counter-strike", "name": "Counter-Strike", "cover": ""},
    {"id": "rocket-league", "name": "Rocket League", "cover": ""},
    {"id": "gta-v", "name": "GTA V", "cover": ""},
    {"id": "overwatch", "name": "Overwatch", "cover": ""},
    {"id": "fifa-23", "name": "FIFA 23", "cover": ""},
]

@games_api_bp.route("/api/games/search")
def search_games():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify({"success": True, "results": FALLBACK_GAMES})
    try:
        params = {"search": q, "page_size": 8}
        if RAWG_API_KEY:
            params["key"] = RAWG_API_KEY
        resp = requests.get(RAWG_BASE_URL, params=params, timeout=4)
        resp.raise_for_status()
        data = resp.json()
        results = []
        for g in data.get("results", []):
            results.append({
                "id": g.get("slug", ""),
                "name": g.get("name", ""),
                "cover": g.get("background_image", "")
            })
        return jsonify({"success": True, "results": results})
    except Exception:
        # Fallback bei Fehler
        return jsonify({"success": True, "results": FALLBACK_GAMES})
