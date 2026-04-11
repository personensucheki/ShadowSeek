from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import logging

from flask import Blueprint, jsonify, render_template, request
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models import EinnahmeInfo
from app.services.currency import convert_eur
from app.services.request_validation import ValidationError, parse_pagination
from app.services.revenue_events import serialize_revenue_event


dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger("pulse_dashboard")

@dashboard_bp.route("/pulse")
@dashboard_bp.route("/dashboard")
def dashboard():
    return render_template("pulse.html")


def _empty_summary_payload(labels, collector_status="waiting"):
    return {
        "labels": labels,
        "values": [0.0 for _ in labels],
        "top_gifter": [],
        "latest": [],
        "total_revenue": 0.0,
        "today_revenue": 0.0,
        "active_creators": 0,
        "record_count": 0,
        "platform_totals": [],
        "collector_status": collector_status,
    }


@dashboard_bp.route("/api/einnahmen/summary")
def einnahmen_summary():
    today = datetime.utcnow().date()
    days = [today - timedelta(days=index) for index in range(13, -1, -1)]
    labels = [day.strftime("%d.%m.") for day in days]
    try:
        values: list[float] = []

        for day in days:
            total = (
                EinnahmeInfo.query.filter(func.date(EinnahmeInfo.captured_at) == day)
                .with_entities(func.sum(EinnahmeInfo.estimated_revenue))
                .scalar()
                or 0
            )
            values.append(float(total))

        total_revenue = float(
            EinnahmeInfo.query.with_entities(func.sum(EinnahmeInfo.estimated_revenue)).scalar() or 0
        )
        today_revenue = float(values[-1] if values else 0)
        record_count = int(
            EinnahmeInfo.query.with_entities(func.count(EinnahmeInfo.id)).scalar() or 0
        )
        active_creators = int(
            EinnahmeInfo.query.with_entities(func.count(func.distinct(EinnahmeInfo.username))).scalar()
            or 0
        )

        top_gifter_rows = (
            EinnahmeInfo.query.with_entities(EinnahmeInfo.username, func.sum(EinnahmeInfo.estimated_revenue))
            .group_by(EinnahmeInfo.username)
            .order_by(func.sum(EinnahmeInfo.estimated_revenue).desc())
            .limit(5)
            .all()
        )
        top_gifter = [
            {"name": source or "?", "sum": float(total)} for source, total in top_gifter_rows
        ]

        limit, offset = parse_pagination(request.args, default_limit=12, max_limit=100)
        latest = EinnahmeInfo.query.order_by(EinnahmeInfo.captured_at.desc()).offset(offset).limit(limit).all()
        latest_list = []
        for entry in latest:
            row = serialize_revenue_event(entry)
            usd = convert_eur(entry.estimated_revenue, "USD")
            row["platform"] = entry.platform.title()
            row["betrag_usd"] = round(usd, 2) if usd else None
            latest_list.append(row)

        grouped_types = (
            EinnahmeInfo.query.with_entities(EinnahmeInfo.platform, func.sum(EinnahmeInfo.estimated_revenue))
            .group_by(EinnahmeInfo.platform)
            .all()
        )
        platform_totals_map: defaultdict[str, float] = defaultdict(float)
        for platform, total in grouped_types:
            platform_totals_map[platform] += float(total or 0)

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
    except SQLAlchemyError:
        logger.exception("Pulse summary unavailable because revenue data could not be loaded.")
        return jsonify(_empty_summary_payload(labels, collector_status="unavailable"))
    except ValidationError as error:
        return jsonify({"success": False, "errors": error.errors}), 400
