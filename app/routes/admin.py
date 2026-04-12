from __future__ import annotations

from urllib.parse import urlencode

from flask import Blueprint, g, redirect, render_template, request, url_for
from sqlalchemy import func

from app.extensions.main import db
from app.models import SearchLog, User
from app.rbac_helpers import login_required, role_required
from app.services.admin_console import (
    add_discount_entry,
    load_admin_console_state,
    update_console_settings,
    update_maintenance_notice,
)
from app.services.billing import PLAN_DEFINITIONS


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

EDIT_ROLES = ("user", "moderator", "admin", "super_admin")
EDIT_STATUSES = ("inactive", "trialing", "active", "past_due", "canceled")


def _redirect_with_notice(message: str, level: str = "info"):
    query = urlencode({"notice": message, "level": level})
    return redirect(f"{url_for('admin.admin_dashboard')}?{query}")


def _can_manage_admins(actor: User) -> bool:
    return actor.role in {"admin", "super_admin"}


def _can_manage_roles(actor: User) -> bool:
    return actor.role == "super_admin"


def _build_dashboard_context():
    actor = g.current_user
    console_state = load_admin_console_state()

    user_rows = (
        User.query.order_by(User.created_at.desc())
        .limit(18)
        .all()
    )

    role_rows = (
        db.session.query(User.role, func.count(User.id))
        .group_by(User.role)
        .all()
    )

    plan_rows = (
        db.session.query(User.plan_code, func.count(User.id))
        .filter(User.plan_code.isnot(None))
        .group_by(User.plan_code)
        .all()
    )

    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    paid_users = User.query.filter(User.subscription_status.in_(("active", "trialing"))).count()
    # SearchLog has a model field named "query", so using SearchLog.query would
    # resolve to that column instead of Flask-SQLAlchemy's query descriptor.
    recent_searches = db.session.query(func.count(SearchLog.id)).scalar() or 0

    return {
        "admin_actor": actor,
        "admin_notice": request.args.get("notice", "").strip(),
        "admin_notice_level": request.args.get("level", "info").strip() or "info",
        "admin_settings": console_state["settings"],
        "maintenance_notice": console_state["maintenance_notice"],
        "discount_entries": console_state["discounts"],
        "user_rows": user_rows,
        "role_stats": {role: count for role, count in role_rows},
        "plan_stats": {plan or "ohne_plan": count for plan, count in plan_rows},
        "plan_definitions": PLAN_DEFINITIONS,
        "edit_roles": EDIT_ROLES,
        "edit_statuses": EDIT_STATUSES,
        "dashboard_metrics": {
            "total_users": total_users,
            "active_users": active_users,
            "paid_users": paid_users,
            "recent_searches": recent_searches,
        },
        "can_manage_admins": _can_manage_admins(actor),
        "can_manage_roles": _can_manage_roles(actor),
    }


@admin_bp.route("/subscription")
@login_required
def subscription():
    return redirect(url_for("billing.billing_page"))


@admin_bp.route("/")
@login_required
@role_required("admin", "super_admin", "moderator")
def admin_dashboard():
    return render_template("admin.html", **_build_dashboard_context())


@admin_bp.route("/settings", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def save_settings():
    update_console_settings(request.form)
    return _redirect_with_notice("Admin-Settings gespeichert.", "success")


@admin_bp.route("/maintenance", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def save_maintenance_notice():
    update_maintenance_notice(request.form, g.current_user.username)
    return _redirect_with_notice("Wartungsnachricht aktualisiert.", "success")


@admin_bp.route("/discounts", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def create_discount():
    try:
        add_discount_entry(request.form, g.current_user.username)
    except ValueError as error:
        return _redirect_with_notice(str(error), "error")
    return _redirect_with_notice("Rabattaktion gespeichert.", "success")


@admin_bp.route("/users/<int:user_id>/profile", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def update_user_profile(user_id: int):
    actor = g.current_user
    user = User.query.get_or_404(user_id)

    next_role = (request.form.get("role") or user.role).strip()
    next_plan = (request.form.get("plan_code") or "").strip() or None
    next_status = (request.form.get("subscription_status") or "").strip() or None

    if next_role not in EDIT_ROLES:
        return _redirect_with_notice("Ungueltige Rolle.", "error")
    if next_status and next_status not in EDIT_STATUSES:
        return _redirect_with_notice("Ungueltiger Abo-Status.", "error")
    if next_plan and next_plan not in PLAN_DEFINITIONS:
        return _redirect_with_notice("Ungueltiger Plan.", "error")
    if not _can_manage_roles(actor) and next_role != user.role:
        return _redirect_with_notice("Nur Super-Admins duerfen Rollen aendern.", "error")
    if user.id == actor.id and next_role != user.role:
        return _redirect_with_notice("Eigene Rolle wird hier nicht geaendert.", "error")

    user.role = next_role
    user.plan_code = next_plan
    user.subscription_status = next_status
    db.session.commit()
    return _redirect_with_notice(f"Nutzer {user.username} aktualisiert.", "success")


@admin_bp.route("/users/<int:user_id>/toggle-ban", methods=["POST"])
@login_required
@role_required("admin", "super_admin")
def toggle_user_ban(user_id: int):
    actor = g.current_user
    user = User.query.get_or_404(user_id)

    if user.id == actor.id:
        return _redirect_with_notice("Eigenen Account kannst du hier nicht sperren.", "error")
    if user.role == "super_admin" and actor.role != "super_admin":
        return _redirect_with_notice("Nur Super-Admins duerfen Super-Admins sperren.", "error")

    user.is_active = not user.is_active
    db.session.commit()
    action = "entsperrt" if user.is_active else "gesperrt"
    return _redirect_with_notice(f"Nutzer {user.username} wurde {action}.", "success")
