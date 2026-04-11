from flask import Blueprint, flash, redirect, render_template, session, url_for


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
def admin_dashboard():
    if not session.get("user_id"):
        flash("Nur fuer Admins zugaenglich.", "danger")
        return redirect(url_for("search.home"))
    return render_template("admin.html")
