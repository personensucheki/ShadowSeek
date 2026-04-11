from flask import Blueprint, jsonify, request, send_file
from app.models import EinnahmeInfo
from sqlalchemy import func
import csv
from io import StringIO

export_bp = Blueprint("export", __name__)

@export_bp.route("/api/einnahmen/export.csv")
def export_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Zeitpunkt", "User", "Betrag", "Typ", "Details"])
    for e in EinnahmeInfo.query.order_by(EinnahmeInfo.zeitpunkt.desc()).all():
        cw.writerow([
            e.zeitpunkt.strftime("%d.%m.%Y %H:%M"),
            e.quelle or "",
            f"{e.betrag:.2f}",
            e.typ,
            e.details or ""
        ])
    output = si.getvalue()
    return send_file(
        StringIO(output),
        mimetype="text/csv",
        as_attachment=True,
        download_name="einnahmen.csv"
    )
