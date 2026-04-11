from flask import Blueprint, jsonify, request
from app.models import EinnahmeInfo
from sqlalchemy import func
from datetime import datetime

api_bp = Blueprint("einnahmen_api", __name__)

@api_bp.route("/api/einnahmen/")
def einnahmen_list():
    args = request.args
    query = EinnahmeInfo.query
    # Filter
    if args.get("user"):
        query = query.filter(EinnahmeInfo.quelle == args["user"])
    if args.get("typ"):
        query = query.filter(EinnahmeInfo.typ == args["typ"])
    if args.get("min"):
        query = query.filter(EinnahmeInfo.betrag >= float(args["min"]))
    if args.get("max"):
        query = query.filter(EinnahmeInfo.betrag <= float(args["max"]))
    if args.get("from"):
        dt = datetime.strptime(args["from"], "%Y-%m-%d")
        query = query.filter(EinnahmeInfo.zeitpunkt >= dt)
    if args.get("to"):
        dt = datetime.strptime(args["to"], "%Y-%m-%d")
        query = query.filter(EinnahmeInfo.zeitpunkt <= dt)
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
