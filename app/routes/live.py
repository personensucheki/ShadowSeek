import secrets

from flask import Blueprint, abort, render_template, request

from app.models import LiveGift, LiveStream, User
from app.rbac_helpers import login_required

live_bp = Blueprint("live", __name__)


@live_bp.route("/live")
@login_required
def live_page():
    categories = [
        "Games",
        "Just Talk",
        "Just Chatting",
        "Dating",
    ]
    stream_key = secrets.token_urlsafe(18)
    ingest_url = f"rtmp://{request.host}/live"
    return render_template(
        "live.html",
        categories=categories,
        stream_key=stream_key,
        ingest_url=ingest_url,
    )


@live_bp.route("/live/view/<int:stream_id>")
@login_required
def live_viewer(stream_id: int):
    stream_model = LiveStream.query.get(stream_id)
    if not stream_model:
        abort(404)

    gift_rows = LiveGift.query.filter(LiveGift.stream_id == stream_id).all()
    totals = {}
    for gift in gift_rows:
        totals[gift.user_id] = totals.get(gift.user_id, 0) + int(gift.amount or 0)

    supporters = []
    if totals:
        sorted_totals = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:3]
        users = {
            user.id: user
            for user in User.query.filter(User.id.in_([uid for uid, _ in sorted_totals])).all()
        }
        for rank, (user_id, gifts) in enumerate(sorted_totals, start=1):
            user = users.get(user_id)
            supporters.append(
                {
                    "rank": rank,
                    "name": user.username if user else f"User {user_id}",
                    "gifts": gifts,
                }
            )

    stream = {
        "id": stream_model.id,
        "title": stream_model.title,
        "category": stream_model.category,
        "viewer_count": 0,
        "supporters": supporters,
    }
    return render_template("live_viewer.html", stream=stream)

