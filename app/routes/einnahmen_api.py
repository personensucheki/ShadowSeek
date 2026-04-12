from flask import Blueprint, request
from app.services.response_utils import api_success, api_error
from app.models import EinnahmeInfo
from app.services.request_validation import ValidationError, parse_date, parse_float, parse_pagination
from app.services.revenue_events import serialize_revenue_event

api_bp = Blueprint("einnahmen_api", __name__)

@api_bp.route("/api/einnahmen/")
def einnahmen_list():
    try:
        args = request.args
        query = EinnahmeInfo.query
        if args.get("user"):
            user = args["user"].strip()
            if not user:
                raise ValidationError({"user": "Must not be empty."})
            query = query.filter(EinnahmeInfo.username == user)
        if args.get("typ"):
            query = query.filter(EinnahmeInfo.typ == args["typ"].strip().lower())
        if args.get("platform"):
            query = query.filter(EinnahmeInfo.platform == args["platform"].strip().lower())
        if args.get("min"):
            query = query.filter(EinnahmeInfo.estimated_revenue >= parse_float(args["min"], "min", minimum=0))
        if args.get("max"):
            query = query.filter(EinnahmeInfo.estimated_revenue <= parse_float(args["max"], "max", minimum=0))
        if args.get("from"):
            query = query.filter(EinnahmeInfo.captured_at >= parse_date(args["from"], "from"))
        if args.get("to"):
            query = query.filter(EinnahmeInfo.captured_at <= parse_date(args["to"], "to"))
        limit, offset = parse_pagination(args, default_limit=100, max_limit=500)
        einnahmen = query.order_by(EinnahmeInfo.captured_at.desc()).offset(offset).limit(limit).all()
        return api_success([serialize_revenue_event(entry) for entry in einnahmen])
    except ValidationError as error:
        return api_error("Validation error", status=400, errors=error.errors)
