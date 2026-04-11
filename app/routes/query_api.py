import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError

from app.models import EinnahmeInfo
from app.services.pulse_profile_scan import build_query_rows, run_creator_profile_scan
from app.services.search_service import SearchValidationError


query_api_bp = Blueprint("query_api", __name__)
logger = logging.getLogger("einnahmen_query")


def _collect_revenue_query_rows(data):
    try:
        filters = []
        log_filters = {}

        if data.get("nutzername"):
            filters.append(EinnahmeInfo.quelle.ilike(f"%{data['nutzername']}%"))
            log_filters["nutzername"] = data["nutzername"]
        if data.get("plattform"):
            filters.append(EinnahmeInfo.typ.ilike(f"{data['plattform'].lower()}%"))
            log_filters["plattform"] = data["plattform"]
        if data.get("kategorie"):
            filters.append(EinnahmeInfo.typ.ilike(f"%{data['kategorie'].lower()}%"))
            log_filters["kategorie"] = data["kategorie"]
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

        logger.info("Einnahmen-Query: %s", log_filters)

        query = EinnahmeInfo.query
        if filters:
            query = query.filter(and_(*filters))

        results = query.order_by(EinnahmeInfo.zeitpunkt.desc()).limit(200).all()
        return [
            {
                "zeitpunkt": entry.zeitpunkt.strftime("%d.%m.%Y %H:%M"),
                "quelle": entry.quelle,
                "betrag": entry.betrag,
                "typ": entry.typ,
                "details": entry.details,
            }
            for entry in results
        ]
    except SQLAlchemyError:
        logger.exception("Revenue query unavailable because earnings data could not be loaded.")
        return []


@query_api_bp.route("/api/einnahmen/query", methods=["POST"])
def einnahmen_query():
    data = request.get_json(force=True)
    return jsonify(_collect_revenue_query_rows(data))


@query_api_bp.route("/api/pulse/query", methods=["POST"])
def pulse_query():
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

    return jsonify(
        {
            "success": True,
            "mode": "revenue",
            "rows": _collect_revenue_query_rows(data),
        }
    )
