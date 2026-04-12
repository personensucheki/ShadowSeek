from __future__ import annotations

import secrets

from flask import Blueprint, render_template, request


live_bp = Blueprint("live", __name__)


@live_bp.route("/live")
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
