from flask import Blueprint, jsonify, request
from app.models import EinnahmeInfo
from sqlalchemy import func
from datetime import datetime

live_api_bp = Blueprint("live_api", __name__)

@live_api_bp.route("/api/live/<platform>")
def live_platform(platform):
    # Plattform-Filter: tiktok, twitch, youtube
    query = EinnahmeInfo.query.filter(EinnahmeInfo.typ.ilike(f"{platform}_%"))
    # Optional: Zeitraum-Filter
    if request.args.get("since"):
        dt = datetime.strptime(request.args["since"], "%Y-%m-%d %H:%M")
        query = query.filter(EinnahmeInfo.zeitpunkt >= dt)
    einnahmen = query.order_by(EinnahmeInfo.zeitpunkt.desc()).limit(100).all()
    return jsonify([
        {
            "zeitpunkt": e.zeitpunkt.strftime("%d.%m.%Y %H:%M"),
            "quelle": e.quelle,
            "betrag": e.betrag,
            "typ": e.typ,
            "details": e.details,
        }
        for e in einnahmen
    ])
