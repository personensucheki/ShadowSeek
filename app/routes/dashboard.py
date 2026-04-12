from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
import logging

from app.services.response_utils import api_success

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError

from app.models import EinnahmeInfo, User
from app.services.billing import billing_enabled, get_user_entitlements
from app.services.feature_gating import feature_required
from app.services.permissions import FEATURE_PULSE
from app.services.request_validation import ValidationError, parse_pagination
from app.services.revenue_events import serialize_revenue_event


dashboard_bp = Blueprint("dashboard", __name__)
logger = logging.getLogger("pulse_dashboard")


@dashboard_bp.route("/pulse")
@dashboard_bp.route("/dashboard")
def dashboard():
    from app.services.permissions import resolve_effective_plan_code, PLAN_ABO_2, PLAN_ABO_3, PLAN_ABO_4
    from flask import g
    user = getattr(g, "current_user", None)
    plan_code = resolve_effective_plan_code(user)
    allowed_plans = {PLAN_ABO_2, PLAN_ABO_3, PLAN_ABO_4}
    if not billing_enabled():
        return render_template("pulse.html")
    if plan_code not in allowed_plans:
        return render_template("pulse.html", pulse_locked=True)
    return render_template("pulse.html", pulse_locked=False)


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
    import logging
    logging.warning("[TRACE] /api/einnahmen/summary route ENTRY")
    today = datetime.utcnow().date()
    days = [today - timedelta(days=index) for index in range(13, -1, -1)]
    labels = [day.strftime("%d.%m.") for day in days]
    try:
        logging.warning("[TRACE] /api/einnahmen/summary before main logic")
        # Zeitraum für die letzten 14 Tage
        start_dt = datetime.combine(days[0], datetime.min.time())
        end_dt = datetime.combine(days[-1] + timedelta(days=1), datetime.min.time())
        base_query = EinnahmeInfo.query.filter(
            EinnahmeInfo.captured_at.between(start_dt, end_dt)
        )
        logging.warning("[TRACE] /api/einnahmen/summary after base_query")
        daily_rows = (
            base_query.with_entities(
                func.date(EinnahmeInfo.captured_at).label("day"),
                func.sum(EinnahmeInfo.estimated_revenue).label("total"),
            )
            .group_by(func.date(EinnahmeInfo.captured_at))
            .all()
        )
        logging.warning(f"[TRACE] /api/einnahmen/summary after daily_rows: {daily_rows}")
        totals_by_day = {str(row.day): float(row.total or 0.0) for row in daily_rows}
        values = [totals_by_day.get(day.isoformat(), 0.0) for day in days]
        total_revenue = float(
            EinnahmeInfo.query.with_entities(func.sum(EinnahmeInfo.estimated_revenue)).scalar()
            or 0.0
        )
        today_revenue = float(values[-1] if values else 0.0)
        record_count = int(
            EinnahmeInfo.query.with_entities(func.count(EinnahmeInfo.id)).scalar() or 0
        )
        active_creators = int(
            EinnahmeInfo.query.with_entities(func.count(func.distinct(EinnahmeInfo.username))).scalar()
            or 0
        )
        logging.warning("[TRACE] /api/einnahmen/summary after stats queries")
        top_creator_rows = (
            EinnahmeInfo.query.with_entities(
                EinnahmeInfo.username,
                func.sum(EinnahmeInfo.estimated_revenue).label("total"),
            )
            .group_by(EinnahmeInfo.username)
            .order_by(func.sum(EinnahmeInfo.estimated_revenue).desc())
            .limit(5)
            .all()
        )
        logging.warning(f"[TRACE] /api/einnahmen/summary after top_creator_rows: {top_creator_rows}")
        top_gifter = [
            {"name": username or "?", "sum": float(total or 0.0)}
            for username, total in top_creator_rows
        ]
        limit, offset = parse_pagination(request.args, default_limit=12, max_limit=100)
        latest_entries = (
            EinnahmeInfo.query.order_by(EinnahmeInfo.captured_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        logging.warning(f"[TRACE] /api/einnahmen/summary after latest_entries: {latest_entries}")
        latest_list = []
        for entry in latest_entries:
            row = serialize_revenue_event(entry)
            row["platform"] = (entry.platform or "unknown").title()
            row["details"] = entry.details or entry.source or ""
            row["captured_at"] = entry.captured_at.strftime("%d.%m.%Y %H:%M")
            latest_list.append(row)
        grouped_platforms = (
            EinnahmeInfo.query.with_entities(
                EinnahmeInfo.platform,
                func.sum(EinnahmeInfo.estimated_revenue).label("total"),
            )
            .group_by(EinnahmeInfo.platform)
            .all()
        )
        logging.warning(f"[TRACE] /api/einnahmen/summary after grouped_platforms: {grouped_platforms}")
        platform_totals_map: defaultdict[str, float] = defaultdict(float)
        for platform, total in grouped_platforms:
            platform_totals_map[platform or "unknown"] += float(total or 0.0)
        platform_totals = [
            {"platform": platform.title(), "total": round(total, 2)}
            for platform, total in sorted(platform_totals_map.items(), key=lambda item: item[1], reverse=True)
        ]
        logging.warning("[TRACE] /api/einnahmen/summary before return api_success")
        return api_success({
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
        })
    except Exception as exc:
        import traceback
        logging.error(f"[TRACE] /api/einnahmen/summary exception: {type(exc).__name__}: {exc}\n{traceback.format_exc()}")
        return api_success(_empty_summary_payload(labels, collector_status="waiting"))
