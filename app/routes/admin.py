
from flask import Blueprint, redirect, render_template, url_for
from app.rbac_helpers import login_required, role_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# Subscription-Ansicht/Karten
@admin_bp.route("/subscription")
@login_required
def subscription():
    return redirect(url_for("billing.billing_page"))


@admin_bp.route("/")
@login_required
@role_required('admin', 'super_admin')
def admin_dashboard():
    return render_template("admin.html")
