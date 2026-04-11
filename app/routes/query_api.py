import logging
from flask import Blueprint, request, jsonify
from app.models import EinnahmeInfo
from sqlalchemy import and_, func
from datetime import datetime

query_api_bp = Blueprint("query_api", __name__)
logger = logging.getLogger("einnahmen_query")

@query_api_bp.route("/api/einnahmen/query", methods=["POST"])
def einnahmen_query():
    data = request.get_json(force=True)
    filters = []
    log_filters = {}
    # Nutzername
    if data.get("nutzername"):
        filters.append(EinnahmeInfo.quelle.ilike(f"%{data['nutzername']}%"))
        log_filters["nutzername"] = data["nutzername"]
    # Plattform
    if data.get("plattform"):
        filters.append(EinnahmeInfo.typ.ilike(f"{data['plattform'].lower()}%"))
        log_filters["plattform"] = data["plattform"]
    # Kategorie
    if data.get("kategorie"):
        filters.append(EinnahmeInfo.typ.ilike(f"%{data['kategorie'].lower()}%"))
        log_filters["kategorie"] = data["kategorie"]
    # Datumsspanne
    if data.get("von"):
        try:
            dt = datetime.strptime(data["von"], "%Y-%m-%d")
            filters.append(EinnahmeInfo.zeitpunkt >= dt)
            log_filters["von"] = data["von"]
        except Exception:
            pass
    if data.get("bis"):
        try:
            dt = datetime.strptime(data["bis"], "%Y-%m-%d")
            filters.append(EinnahmeInfo.zeitpunkt <= dt)
            log_filters["bis"] = data["bis"]
        except Exception:
            pass
    # Einnahmehöhe
    if data.get("min"):
        try:
            filters.append(EinnahmeInfo.betrag >= float(data["min"]))
            log_filters["min"] = data["min"]
        except Exception:
            pass
    if data.get("max"):
        try:
            filters.append(EinnahmeInfo.betrag <= float(data["max"]))
            log_filters["max"] = data["max"]
        except Exception:
            pass
    # Logging
    logger.info(f"Einnahmen-Query: {log_filters}")
    # Query
    query = EinnahmeInfo.query
    if filters:
        query = query.filter(and_(*filters))
    results = query.order_by(EinnahmeInfo.zeitpunkt.desc()).limit(200).all()
    return jsonify([
        {
            "zeitpunkt": e.zeitpunkt.strftime("%d.%m.%Y %H:%M"),
            "quelle": e.quelle,
            "betrag": e.betrag,
            "typ": e.typ,
            "details": e.details,
        }
        for e in results
    ])
