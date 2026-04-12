import logging

from flask import Blueprint, jsonify, request, session
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from app.models import EinnahmeInfo, User
from app.services.billing import billing_enabled, get_user_entitlements
from app.services.pulse_profile_scan import build_query_rows, run_creator_profile_scan
from app.services.request_validation import ValidationError, parse_date, parse_float, parse_pagination
from app.services.revenue_events import serialize_revenue_event
from app.services.search_service import SearchValidationError


query_api_bp = Blueprint("query_api", __name__)
logger = logging.getLogger("einnahmen_query")


def _collect_revenue_query_rows(data):
    try:
        limit, offset = parse_pagination(data, default_limit=100, max_limit=500)
        filters = []
        log_filters = {}

        if data.get("nutzername"):
            username = str(data["nutzername"]).strip()
            if not username:
                raise ValidationError({"nutzername": "Must not be empty."})
            if len(username) > 64:
                raise ValidationError({"nutzername": "Must not exceed 64 characters."})
            filters.append(EinnahmeInfo.username.ilike(f"%{username}%"))
            log_filters["nutzername"] = data["nutzername"]
        if data.get("plattform"):
            filters.append(EinnahmeInfo.platform == str(data["plattform"]).strip().lower())
            log_filters["plattform"] = data["plattform"]
        if data.get("kategorie"):
            # TODO remove legacy mapping
            filters.append(EinnahmeInfo.typ.ilike(f"%{str(data['kategorie']).strip().lower()}%"))
            log_filters["kategorie"] = data["kategorie"]
        if data.get("von"):
            dt = parse_date(str(data["von"]).strip(), "von")
            filters.append(EinnahmeInfo.captured_at >= dt)
            log_filters["von"] = data["von"]
        if data.get("bis"):
            dt = parse_date(str(data["bis"]).strip(), "bis")
            filters.append(EinnahmeInfo.captured_at <= dt)
            log_filters["bis"] = data["bis"]
        if data.get("min"):
            filters.append(EinnahmeInfo.estimated_revenue >= parse_float(data["min"], "min", minimum=0))
            log_filters["min"] = data["min"]
        if data.get("max"):
            filters.append(EinnahmeInfo.estimated_revenue <= parse_float(data["max"], "max", minimum=0))
            log_filters["max"] = data["max"]

        logger.info("Einnahmen-Query: %s", log_filters)

        query = EinnahmeInfo.query
        if filters:
            query = query.filter(and_(*filters))

        results = query.order_by(EinnahmeInfo.captured_at.desc()).offset(offset).limit(limit).all()
        return [serialize_revenue_event(entry) for entry in results]
    except ValidationError as error:
        return {"_validation_error": error.errors}
    except SQLAlchemyError:
        logger.exception("Revenue query unavailable because earnings data could not be loaded.")
        return []


@query_api_bp.route("/api/einnahmen/query", methods=["POST"])
def einnahmen_query():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Invalid JSON body."}), 400
    rows = _collect_revenue_query_rows(data)
    if isinstance(rows, dict) and rows.get("_validation_error"):
        return jsonify({"success": False, "errors": rows["_validation_error"]}), 400
    return jsonify(rows)


@query_api_bp.route("/api/pulse/query", methods=["POST"])
def pulse_query():
    if billing_enabled():
        user_id = session.get("user_id")
        from app.extensions.main import db
        user = db.session.get(User, user_id) if user_id else None
        entitlements = get_user_entitlements(user)
        if not entitlements["pulse_allowed"]:
            return jsonify({"success": False, "error": "Pulse ist in deinem aktuellen Abo nicht freigeschaltet."}), 403
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        return jsonify({"success": False, "error": "Invalid JSON body."}), 400

    creator_query = (data.get("nutzername") or "").strip()
    if creator_query:
        try:
            scan_result = run_creator_profile_scan(
                creator_query,
                request.host_url,
                platform_slug=data.get("plattform"),
                deep_search=True,
            )
        except SearchValidationError as error:
            return jsonify({"success": False, "errors": error.errors}), 400

        return jsonify(
            {
                "success": True,
                "mode": "profile_scan",
                "query": scan_result.get("query", {}),
                "summary": scan_result.get("summary", {}),
                "meta": scan_result.get("meta", {}),
                "rows": build_query_rows(scan_result),
            }
        )

    rows = _collect_revenue_query_rows(data)
    if isinstance(rows, dict) and rows.get("_validation_error"):
        return jsonify({"success": False, "errors": rows["_validation_error"]}), 400
    return jsonify(
        {
            "success": True,
            "mode": "revenue",
            "rows": rows,
        }
    )


@query_api_bp.route("/api/pulse/search", methods=["POST"])
def pulse_search():
    return pulse_query()
