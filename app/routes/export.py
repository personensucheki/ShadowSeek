from flask import Blueprint, send_file
from app.models import EinnahmeInfo
import csv
from io import StringIO

export_bp = Blueprint("export", __name__)

@export_bp.route("/api/einnahmen/export.csv")
def export_csv():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["Captured At", "Platform", "Username", "Display Name", "Estimated Revenue", "Currency", "Source", "Confidence"])
    for e in EinnahmeInfo.query.order_by(EinnahmeInfo.captured_at.desc()).all():
        cw.writerow([
            e.captured_at.isoformat(),
            e.platform,
            e.username,
            e.display_name or "",
            f"{e.estimated_revenue:.2f}",
            e.currency,
            e.source,
            e.confidence,
        ])
    output = si.getvalue()
    return send_file(
        StringIO(output),
        mimetype="text/csv",
        as_attachment=True,
        download_name="einnahmen.csv"
    )
