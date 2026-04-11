
from flask import Blueprint, flash, redirect, render_template, session, url_for
from app.rbac_helpers import login_required, role_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@role_required('admin', 'super_admin')
def admin_dashboard():
    return render_template("admin.html")
