
from flask import Blueprint, flash, redirect, render_template, session, url_for, current_app
from app.rbac_helpers import login_required, role_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# Subscription-Ansicht/Karten
@admin_bp.route("/subscription")
@login_required
def subscription():
    plans = current_app.config.get('PLANS', {})
    return render_template('subscription.html', plans=plans)


@admin_bp.route("/")
@login_required
@role_required('admin', 'super_admin')
def admin_dashboard():
    return render_template("admin.html")
