from __future__ import annotations

import secrets

from flask import Blueprint, render_template, session, redirect, url_for, request

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

# Viewer-Seite im modernen Stil
@live_bp.route('/live/view/<string:stream_id>')
def live_viewer(stream_id):
    # TODO: Stream-Metadaten aus DB/API holen
    # Dummy-Daten für Design
    stream = {
        'id': stream_id,
        'title': 'ShadowSeek Live: OSINT Deep Dive',
        'category': 'Tech',
        'viewer_count': 42,
        'supporters': [
            {'rank': 1, 'name': 'Alice', 'gifts': 100},
            {'rank': 2, 'name': 'Bob', 'gifts': 50},
            {'rank': 3, 'name': 'Charlie', 'gifts': 20},
        ]
    }
    return render_template('live_viewer.html', stream=stream)
