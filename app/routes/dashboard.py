from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, render_template
from sqlalchemy import func

from app.models import EinnahmeInfo
from app.services.currency import convert_eur


dashboard_bp = Blueprint("dashboard", __name__)


def _platform_from_type(entry_type: str | None) -> str:
    value = (entry_type or "unknown").strip().lower()
    return value.split("_", 1)[0] if "_" in value else value


@dashboard_bp.route("/pulse")
@dashboard_bp.route("/dashboard")
def dashboard():
    return render_template("pulse.html")


@dashboard_bp.route("/api/einnahmen/summary")
def einnahmen_summary():
    today = datetime.utcnow().date()
    days = [today - timedelta(days=index) for index in range(13, -1, -1)]
    labels = [day.strftime("%d.%m.") for day in days]
    values: list[float] = []

    for day in days:
        total = (
            EinnahmeInfo.query.filter(func.date(EinnahmeInfo.zeitpunkt) == day)
            .with_entities(func.sum(EinnahmeInfo.betrag))
            .scalar()
            or 0
        )
        values.append(float(total))

    total_revenue = float(
        EinnahmeInfo.query.with_entities(func.sum(EinnahmeInfo.betrag)).scalar() or 0
    )
    today_revenue = float(values[-1] if values else 0)
    record_count = int(EinnahmeInfo.query.with_entities(func.count(EinnahmeInfo.id)).scalar() or 0)
    active_creators = int(
        EinnahmeInfo.query.with_entities(func.count(func.distinct(EinnahmeInfo.quelle))).scalar() or 0
    )

    top_gifter_rows = (
        EinnahmeInfo.query.with_entities(EinnahmeInfo.quelle, func.sum(EinnahmeInfo.betrag))
        .group_by(EinnahmeInfo.quelle)
        .order_by(func.sum(EinnahmeInfo.betrag).desc())
        .limit(5)
        .all()
    )
    top_gifter = [{"name": source or "?", "sum": float(total)} for source, total in top_gifter_rows]

    latest = EinnahmeInfo.query.order_by(EinnahmeInfo.zeitpunkt.desc()).limit(12).all()
    latest_list = []
    for entry in latest:
        usd = convert_eur(entry.betrag, "USD")
        latest_list.append(
            {
                "zeitpunkt": entry.zeitpunkt.strftime("%d.%m.%Y %H:%M"),
                "quelle": entry.quelle,
                "betrag": entry.betrag,
                "betrag_usd": round(usd, 2) if usd else None,
                "typ": entry.typ,
                "platform": _platform_from_type(entry.typ).title(),
                "details": entry.details,
            }
        )

    grouped_types = (
        EinnahmeInfo.query.with_entities(EinnahmeInfo.typ, func.sum(EinnahmeInfo.betrag))
        .group_by(EinnahmeInfo.typ)
        .all()
    )
    platform_totals_map: defaultdict[str, float] = defaultdict(float)
    for entry_type, total in grouped_types:
        platform_totals_map[_platform_from_type(entry_type)] += float(total or 0)

    platform_totals = [
        {"platform": platform.title(), "total": round(total, 2)}
        for platform, total in sorted(
            platform_totals_map.items(),
            key=lambda item: item[1],
            reverse=True,
        )
    ]

    return jsonify(
        {
            "labels": labels,
            "values": values,
            "top_gifter": top_gifter,
            "latest": latest_list,
            "total_revenue": round(total_revenue, 2),
            "today_revenue": round(today_revenue, 2),
            "active_creators": active_creators,
            "record_count": record_count,
            "platform_totals": platform_totals,
            "collector_status": "active" if record_count else "waiting",
        }
    )
