from datetime import datetime

from flask import Blueprint, jsonify, request

from app.models import EinnahmeInfo
from app.services.pulse_profile_scan import build_live_rows, run_creator_profile_scan
from app.services.search_service import SearchValidationError


live_api_bp = Blueprint("live_api", __name__)


def _collect_live_rows(platform):
    query = EinnahmeInfo.query.filter(EinnahmeInfo.typ.ilike(f"{platform}_%"))
    if request.args.get("since"):
        dt = datetime.strptime(request.args["since"], "%Y-%m-%d %H:%M")
        query = query.filter(EinnahmeInfo.zeitpunkt >= dt)

    einnahmen = query.order_by(EinnahmeInfo.zeitpunkt.desc()).limit(100).all()
    return [
        {
            "zeitpunkt": entry.zeitpunkt.strftime("%d.%m.%Y %H:%M"),
            "quelle": entry.quelle,
            "betrag": entry.betrag,
            "typ": entry.typ,
            "details": entry.details,
        }
        for entry in einnahmen
    ]


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
