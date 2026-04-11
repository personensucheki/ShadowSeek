from flask import Blueprint, render_template, session, redirect, url_for, flash

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def admin_dashboard():
    # Hier später: Access Control für Admins
    if not session.get('user_id'):
        flash('Nur für Admins zugänglich!', 'danger')
        return redirect(url_for('auth.login'))
    return render_template('admin.html')
