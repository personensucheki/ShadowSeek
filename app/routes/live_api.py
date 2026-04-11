import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app.models import EinnahmeInfo
from app.services.pulse_profile_scan import build_live_rows, run_creator_profile_scan
from app.services.request_validation import ValidationError, parse_pagination
from app.services.revenue_events import serialize_revenue_event
from app.services.search_service import SearchValidationError


live_api_bp = Blueprint("live_api", __name__)
logger = logging.getLogger("pulse_live")


def _collect_live_rows(platform):
    try:
        query = EinnahmeInfo.query.filter(EinnahmeInfo.platform == platform)
        if request.args.get("since"):
            dt = datetime.strptime(request.args["since"], "%Y-%m-%d %H:%M")
            query = query.filter(EinnahmeInfo.captured_at >= dt)
        limit, offset = parse_pagination(request.args, default_limit=100, max_limit=500)
        einnahmen = query.order_by(EinnahmeInfo.captured_at.desc()).offset(offset).limit(limit).all()
        return [serialize_revenue_event(entry) for entry in einnahmen]
    except ValidationError:
        return []
    except SQLAlchemyError:
        logger.exception("Pulse live revenue feed unavailable for platform %s.", platform)
        return []


@live_api_bp.route("/api/live/<platform>")
def live_platform(platform):
    return jsonify(_collect_live_rows(platform))


@live_api_bp.route("/api/pulse/live/<platform>")
def pulse_live_platform(platform):
    creator_query = (request.args.get("creator") or "").strip()
    if creator_query:
        try:
            scan_result = run_creator_profile_scan(
                creator_query,
                request.host_url,
                platform_slug=platform,
                deep_search=True,
            )
        except SearchValidationError as error:
            return jsonify({"success": False, "errors": error.errors}), 400

        return jsonify(
            {
                "success": True,
                "mode": "profile_scan",
                "platform": platform,
                "query": scan_result.get("query", {}),
                "summary": scan_result.get("summary", {}),
                "meta": scan_result.get("meta", {}),
                "rows": build_live_rows(scan_result),
            }
        )

    return jsonify(
        {
            "success": True,
            "mode": "revenue",
            "platform": platform,
            "rows": _collect_live_rows(platform),
        }
    )
