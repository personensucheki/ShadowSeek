from flask import Blueprint, jsonify, render_template
from app.models import EinnahmeInfo
from sqlalchemy import func
from datetime import datetime, timedelta
from app.services.currency import convert_eur

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@dashboard_bp.route("/api/einnahmen/summary")
def einnahmen_summary():
    # Einnahmen pro Tag (letzte 14 Tage)
    today = datetime.utcnow().date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    labels = [d.strftime("%d.%m.") for d in days]
    values = []
    for d in days:
        s = EinnahmeInfo.query.filter(
            func.date(EinnahmeInfo.zeitpunkt) == d
        ).with_entities(func.sum(EinnahmeInfo.betrag)).scalar() or 0
        values.append(float(s))
    # Top Gifter
    top_gifter = (
        EinnahmeInfo.query.with_entities(EinnahmeInfo.quelle, func.sum(EinnahmeInfo.betrag))
        .group_by(EinnahmeInfo.quelle)
        .order_by(func.sum(EinnahmeInfo.betrag).desc())
        .limit(5)
        .all()
    )
    top_gifter = [{"name": q or "?", "sum": float(s)} for q, s in top_gifter]
    # Letzte Einnahmen
    latest = EinnahmeInfo.query.order_by(EinnahmeInfo.zeitpunkt.desc()).limit(10).all()
    latest_list = []
    for e in latest:
        usd = convert_eur(e.betrag, "USD")
        latest_list.append({
            "zeitpunkt": e.zeitpunkt.strftime("%d.%m.%Y %H:%M"),
            "quelle": e.quelle,
            "betrag": e.betrag,
            "betrag_usd": round(usd, 2) if usd else None,
            "typ": e.typ,
            "details": e.details,
        })
    return jsonify({"labels": labels, "values": values, "top_gifter": top_gifter, "latest": latest_list})
