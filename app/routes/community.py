from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for
from sqlalchemy import and_, case, func, or_

from app.extensions.main import db
from app.models import DirectMessage, User
from app.rbac_helpers import login_required, role_required
from app.services.media import resolve_user_avatar_url


community_bp = Blueprint("community", __name__)

ONLINE_WINDOW = timedelta(minutes=5)


def _member_payload(user: User):
    return {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name or user.username,
        "role": user.role,
        "country": user.country or "",
        "city": user.city or "",
        "age": user.age,
        "profile_title": user.profile_title or "",
        "bio": user.bio or "",
        "avatar_url": resolve_user_avatar_url(user),
        "is_online": user.is_online,
        "last_seen_at": user.last_seen_at,
        "created_at": user.created_at,
    }


def _apply_member_filters(users: list[User], args):
    query_text = (args.get("q") or "").strip().lower()
    country = (args.get("country") or "").strip().lower()
    city = (args.get("city") or "").strip().lower()
    role = (args.get("role") or "").strip().lower()
    online = (args.get("online") or "").strip().lower()
    min_age_raw = (args.get("min_age") or "").strip()
    max_age_raw = (args.get("max_age") or "").strip()

    try:
        min_age = int(min_age_raw) if min_age_raw else None
    except ValueError:
        min_age = None
    try:
        max_age = int(max_age_raw) if max_age_raw else None
    except ValueError:
        max_age = None

    filtered = []
    for user in users:
        age = user.age
        haystack = " ".join(
            [
                user.username or "",
                user.display_name or "",
                user.profile_title or "",
                user.bio or "",
                user.country or "",
                user.city or "",
            ]
        ).lower()
        if query_text and query_text not in haystack:
            continue
        if country and country != (user.country or "").strip().lower():
            continue
        if city and city not in (user.city or "").strip().lower():
            continue
        if role and role != (user.role or "").strip().lower():
            continue
        if online == "online" and not user.is_online:
            continue
        if online == "offline" and user.is_online:
            continue
        if min_age is not None and (age is None or age < min_age):
            continue
        if max_age is not None and (age is None or age > max_age):
            continue
        filtered.append(user)
    return filtered


def _sorted_members(users: list[User], sort_key: str):
    if sort_key == "newest":
        return sorted(users, key=lambda user: user.created_at or datetime.min, reverse=True)
    if sort_key == "age_desc":
        return sorted(users, key=lambda user: user.age if user.age is not None else -1, reverse=True)
    if sort_key == "age_asc":
        return sorted(users, key=lambda user: user.age if user.age is not None else 999, reverse=False)
    if sort_key == "country":
        return sorted(users, key=lambda user: ((user.country or "zzz").lower(), (user.display_name or user.username).lower()))
    return sorted(
        users,
        key=lambda user: (
            not user.is_online,
            (user.display_name or user.username).lower(),
        ),
    )


def _distinct_countries():
    rows = (
        db.session.query(User.country)
        .filter(User.country.isnot(None), User.country != "")
        .distinct()
        .order_by(User.country.asc())
        .all()
    )
    return [row[0] for row in rows if row[0]]


def _contacts_for_user(current_user_id: int):
    other_user_id = case(
        (DirectMessage.sender_id == current_user_id, DirectMessage.recipient_id),
        else_=DirectMessage.sender_id,
    )
    rows = (
        db.session.query(
            other_user_id.label("other_user_id"),
            func.max(DirectMessage.created_at).label("last_message_at"),
            func.sum(
                case(
                    (
                        and_(
                            DirectMessage.recipient_id == current_user_id,
                            DirectMessage.read_at.is_(None),
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("unread_count"),
        )
        .filter(
            or_(
                DirectMessage.sender_id == current_user_id,
                DirectMessage.recipient_id == current_user_id,
            )
        )
        .group_by(other_user_id)
        .order_by(func.max(DirectMessage.created_at).desc())
        .all()
    )
    contact_ids = [row.other_user_id for row in rows if row.other_user_id]
    if not contact_ids:
        return []
    users_by_id = {user.id: user for user in User.query.filter(User.id.in_(contact_ids)).all()}
    contacts = []
    for row in rows:
        user = users_by_id.get(row.other_user_id)
        if not user:
            continue
        contacts.append(
            {
                "user": user,
                "avatar_url": resolve_user_avatar_url(user),
                "last_message_at": row.last_message_at,
                "unread_count": int(row.unread_count or 0),
            }
        )
    return contacts


@community_bp.route("/members", methods=["GET"])
@login_required
def members():
    sort_key = (request.args.get("sort") or "online").strip().lower()
    users = (
        User.query
        .filter(User.is_active.is_(True))
        .order_by(User.created_at.desc())
        .all()
    )
    filtered = _apply_member_filters(users, request.args)
    members_payload = [_member_payload(user) for user in _sorted_members(filtered, sort_key)]
    return render_template(
        "members.html",
        members=members_payload,
        filters=request.args,
        country_options=_distinct_countries(),
        online_count=sum(1 for user in members_payload if user["is_online"]),
        total_count=len(members_payload),
    )


@community_bp.route("/messages", methods=["GET"])
@login_required
def messages():
    current_user = g.current_user
    partner_id = request.args.get("user", type=int)
    contacts = _contacts_for_user(current_user.id)

    partner = None
    if partner_id:
        partner = User.query.filter(User.id == partner_id, User.is_active.is_(True)).first()
    elif contacts:
        partner = contacts[0]["user"]

    thread_messages = []
    if partner:
        thread_messages = (
            DirectMessage.query
            .filter(
                or_(
                    and_(
                        DirectMessage.sender_id == current_user.id,
                        DirectMessage.recipient_id == partner.id,
                    ),
                    and_(
                        DirectMessage.sender_id == partner.id,
                        DirectMessage.recipient_id == current_user.id,
                    ),
                )
            )
            .order_by(DirectMessage.created_at.asc())
            .all()
        )
        for message in thread_messages:
            if message.recipient_id == current_user.id and message.read_at is None:
                message.mark_read()
        db.session.commit()

    available_users = (
        User.query
        .filter(User.id != current_user.id, User.is_active.is_(True))
        .order_by(func.coalesce(User.display_name, User.username).asc(), User.username.asc())
        .limit(200)
        .all()
    )

    avatar_lookup = {current_user.id: resolve_user_avatar_url(current_user)}
    for user in available_users:
        avatar_lookup[user.id] = resolve_user_avatar_url(user)
    for contact in contacts:
        avatar_lookup[contact["user"].id] = contact["avatar_url"]
    if partner:
        avatar_lookup[partner.id] = resolve_user_avatar_url(partner)

    return render_template(
        "messages.html",
        contacts=contacts,
        partner=partner,
        thread_messages=thread_messages,
        available_users=available_users,
        avatar_lookup=avatar_lookup,
    )


@community_bp.route("/messages/send", methods=["POST"])
@login_required
def send_message():
    current_user = g.current_user
    recipient_id = request.form.get("recipient_id", type=int)
    body = (request.form.get("body") or "").strip()

    if not recipient_id:
        flash("Bitte einen Empfaenger auswaehlen.", "error")
        return redirect(url_for("community.messages"))
    if not body:
        flash("Nachricht darf nicht leer sein.", "error")
        return redirect(url_for("community.messages", user=recipient_id))
    if len(body) > 4000:
        flash("Nachricht ist zu lang.", "error")
        return redirect(url_for("community.messages", user=recipient_id))

    recipient = User.query.filter(User.id == recipient_id, User.is_active.is_(True)).first()
    if not recipient or recipient.id == current_user.id:
        flash("Empfaenger ist ungueltig.", "error")
        return redirect(url_for("community.messages"))

    db.session.add(
        DirectMessage(
            sender_id=current_user.id,
            recipient_id=recipient.id,
            body=body,
        )
    )
    db.session.commit()
    flash("Nachricht gesendet.", "success")
    return redirect(url_for("community.messages", user=recipient.id))


@community_bp.route("/api/messages/unread", methods=["GET"])
@login_required
def unread_message_count():
    count = (
        DirectMessage.query
        .filter(
            DirectMessage.recipient_id == g.current_user.id,
            DirectMessage.read_at.is_(None),
        )
        .count()
    )
    return jsonify(success=True, unread_count=count)


@community_bp.route("/stats", methods=["GET"])
@login_required
@role_required("admin", "super_admin", "moderator")
def stats():
    users = User.query.filter(User.is_active.is_(True)).all()
    now = datetime.utcnow()
    online_users = [user for user in users if user.is_online]
    members_last_week = [user for user in users if user.created_at and user.created_at >= now - timedelta(days=7)]
    role_counts = Counter((user.role or "user") for user in users)
    country_counts = Counter((user.country or "Unbekannt") for user in users if user.country)
    if not country_counts:
        country_counts["Unbekannt"] = len(users)

    direct_messages_last_7d = (
        DirectMessage.query
        .filter(DirectMessage.created_at >= now - timedelta(days=7))
        .count()
    )
    unread_messages = (
        DirectMessage.query
        .filter(DirectMessage.read_at.is_(None))
        .count()
    )

    newest_members = (
        User.query
        .filter(User.is_active.is_(True))
        .order_by(User.created_at.desc())
        .limit(8)
        .all()
    )

    return render_template(
        "stats.html",
        metrics={
            "total_members": len(users),
            "online_members": len(online_users),
            "new_members_7d": len(members_last_week),
            "messages_7d": direct_messages_last_7d,
            "unread_messages": unread_messages,
        },
        role_counts=dict(role_counts),
        country_counts=country_counts.most_common(8),
        newest_members=newest_members,
        avatar_lookup={user.id: resolve_user_avatar_url(user) for user in newest_members},
    )
