# UI Blueprint: /date-match
from flask import Blueprint, render_template, g
from app.rbac_helpers import login_required

date_match_ui_bp = Blueprint('date_match_ui', __name__, url_prefix=None)

@date_match_ui_bp.route('/date-match', methods=['GET'])
@login_required
def date_match_page():
    return render_template('date_match.html')

# API Blueprint: /api/date-match/*
from flask import Blueprint as ApiBlueprint, request, jsonify
from app.models import User, SwipeAction, Match
from app.extensions.main import db

date_match_api_bp = ApiBlueprint('date_match_api', __name__, url_prefix='/api/date-match')

def api_response(success, data=None, error=None):
    return jsonify({"success": success, "data": data, "error": error})

@date_match_api_bp.route('/discover', methods=['GET'])
@login_required
def discover():
    user_id = g.current_user.id
    swiped = db.session.query(SwipeAction.target_user_id).filter_by(actor_user_id=user_id)
    matched = db.session.query(Match.user_a_id).filter_by(user_b_id=user_id).union(
        db.session.query(Match.user_b_id).filter_by(user_a_id=user_id)
    )
    candidates = User.query.filter(
        User.id != user_id,
        ~User.id.in_(swiped),
        ~User.id.in_(matched)
    ).all()
    data = [{"id": u.id, "username": u.username, "real_name": u.real_name, "age": u.age, "avatar_url": u.avatar_url} for u in candidates]
    return api_response(True, data=data)

@date_match_api_bp.route('/swipe', methods=['POST'])
@login_required
def swipe():
    user_id = g.current_user.id
    payload = request.get_json(silent=True) or {}
    target_user_id = payload.get('target_user_id')
    action = payload.get('action')
    if not target_user_id or not isinstance(target_user_id, int):
        return api_response(False, error="target_user_id fehlt oder ungültig")
    if action not in ("left", "right", "super"):
        return api_response(False, error="Ungültige Aktion")
    if target_user_id == user_id:
        return api_response(False, error="Self-Match nicht erlaubt")
    exists = SwipeAction.query.filter_by(actor_user_id=user_id, target_user_id=target_user_id).first()
    if exists:
        return api_response(False, error="Bereits geswiped")
    swipe = SwipeAction(actor_user_id=user_id, target_user_id=target_user_id, action=action)
    db.session.add(swipe)
    db.session.commit()
    if action in ("right", "super"):
        reciprocal = SwipeAction.query.filter_by(actor_user_id=target_user_id, target_user_id=user_id, action="right").first()
        if reciprocal:
            a, b = sorted([user_id, target_user_id])
            match = Match.query.filter_by(user_a_id=a, user_b_id=b).first()
            if not match:
                match = Match(user_a_id=a, user_b_id=b)
                db.session.add(match)
                db.session.commit()
            return api_response(True, data={"match": True, "user_id": target_user_id})
    return api_response(True, data={"match": False})

@date_match_api_bp.route('/list', methods=['GET'])
@login_required
def match_list():
    user_id = g.current_user.id
    matches = Match.query.filter(
        ((Match.user_a_id == user_id) | (Match.user_b_id == user_id)),
        Match.status == 'active'
    ).all()
    data = []
    for m in matches:
        other_id = m.user_b_id if m.user_a_id == user_id else m.user_a_id
        u = User.query.get(other_id)
        if u:
            data.append({"id": u.id, "username": u.username, "real_name": u.real_name, "age": u.age, "avatar_url": u.avatar_url, "matched_at": m.matched_at})
    return api_response(True, data=data)

@date_match_api_bp.route('/unmatch', methods=['POST'])
@login_required
def unmatch():
    user_id = g.current_user.id
    payload = request.get_json(silent=True) or {}
    target_user_id = payload.get('target_user_id')
    if not target_user_id or not isinstance(target_user_id, int):
        return api_response(False, error="target_user_id fehlt oder ungültig")
    a, b = sorted([user_id, target_user_id])
    match = Match.query.filter_by(user_a_id=a, user_b_id=b, status='active').first()
    if not match:
        return api_response(False, error="Kein aktives Match")
    match.status = 'unmatched'
    db.session.commit()
    return api_response(True, data={"unmatched": True})
