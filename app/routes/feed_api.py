from __future__ import annotations

"""
Feed interaction endpoints (comments/likes/views).

These endpoints are used by the Feed frontend (`app/static/js/feed.js`).
They are intentionally separate from the main feed listing endpoint in `routes/feed.py`.
"""

from flask import Blueprint, request, session
from app.services.response_utils import api_success, api_error

from app.extensions.main import db
from app.models.media_post import MediaPost
from app.models.post_interaction import PostComment, PostLike
from app.models.user import User


feed_api_bp = Blueprint("feed_api", __name__)


def _current_user_id() -> int | None:
    user_id = session.get("user_id")
    if user_id:
        return int(user_id)
    if request.is_json:
        data = request.get_json(silent=True) or {}
        if isinstance(data, dict) and data.get("user_id"):
            try:
                return int(data["user_id"])
            except Exception:
                return None
    return None


@feed_api_bp.get("/api/feed/<int:post_id>/comments")
def get_comments(post_id: int):
    post = db.session.get(MediaPost, post_id)
    if not post:
        return api_error("Post nicht gefunden.", status=404, errors={"code": "not_found"})

    comments = (
        PostComment.query.filter_by(post_id=post_id)
        .order_by(PostComment.created_at.asc())
        .all()
    )

    user_ids = {c.user_id for c in comments}
    users = {u.id: u for u in User.query.filter(User.id.in_(user_ids)).all()} if user_ids else {}

    items = []
    for c in comments:
        user = users.get(c.user_id)
        items.append(
            {
                "id": c.id,
                "user_id": c.user_id,
                "username": user.username if user else "user",
                "display_name": (user.display_name or user.username) if user else "User",
                "content": c.content,
                "created_at": c.created_at.isoformat(),
            }
        )
    return api_success({"items": items})


@feed_api_bp.post("/api/feed/<int:post_id>/comments")
def post_comment(post_id: int):
    user_id = _current_user_id()
    if not user_id:
        return api_error("Nicht eingeloggt.", status=401, errors={"code": "not_authenticated"})

    post = db.session.get(MediaPost, post_id)
    if not post:
        return api_error("Post nicht gefunden.", status=404, errors={"code": "not_found"})

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return api_error("Kommentar darf nicht leer sein.", status=400, errors={"code": "empty"})

    comment = PostComment(post_id=post_id, user_id=user_id, content=content[:500])
    db.session.add(comment)
    db.session.commit()

    user = db.session.get(User, user_id)
    return api_success({
        "comment": {
            "id": comment.id,
            "user_id": user_id,
            "username": user.username if user else "user",
            "display_name": (user.display_name or user.username) if user else "User",
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
        },
    })


@feed_api_bp.post("/api/feed/<int:post_id>/like")
def like_post(post_id: int):
    user_id = _current_user_id()
    if not user_id:
        return api_error("Nicht eingeloggt.", status=401, errors={"code": "not_authenticated"})

    post = db.session.get(MediaPost, post_id)
    if not post:
        return api_error("Post nicht gefunden.", status=404, errors={"code": "not_found"})

    existing = PostLike.query.filter_by(post_id=post_id, user_id=user_id).first()
    if existing:
        db.session.delete(existing)
        liked = False
    else:
        db.session.add(PostLike(post_id=post_id, user_id=user_id))
        liked = True

    db.session.flush()
    like_count = PostLike.query.filter_by(post_id=post_id).count()
    post.like_count = like_count
    db.session.commit()
    return api_success({"liked": liked, "like_count": like_count, "post_id": post_id})


@feed_api_bp.post("/api/feed/<int:post_id>/view")
def view_post(post_id: int):
    # Minimal structured response; view-count persistence can be added later.
    post = db.session.get(MediaPost, post_id)
    if not post:
        return api_error("Post nicht gefunden.", status=404, errors={"code": "not_found"})
    return api_success({"viewed": True, "post_id": post_id})

