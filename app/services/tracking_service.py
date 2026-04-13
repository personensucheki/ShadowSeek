from __future__ import annotations

from datetime import datetime

from app.extensions.main import db
from app.models.osint_engine import Watchlist


def upsert_watchlist_entry(payload: dict) -> Watchlist:
    normalized_username = str(payload.get("normalized_username") or "").strip().lower()
    platform = str(payload.get("platform") or "unknown").strip().lower()
    if not normalized_username:
        raise ValueError("normalized_username is required")

    row = Watchlist.query.filter_by(normalized_username=normalized_username, platform=platform).first()
    if not row:
        row = Watchlist(
            user_id=payload.get("user_id"),
            platform=platform,
            normalized_username=normalized_username,
        )
        db.session.add(row)

    row.last_seen_bio = payload.get("last_seen_bio")
    row.last_seen_avatar_hash = payload.get("last_seen_avatar_hash")
    row.last_seen_links = payload.get("last_seen_links")
    row.last_checked_at = datetime.utcnow()
    db.session.commit()
    return row


def serialize_watchlist_entry(row: Watchlist) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "platform": row.platform,
        "normalized_username": row.normalized_username,
        "last_seen_bio": row.last_seen_bio,
        "last_seen_avatar_hash": row.last_seen_avatar_hash,
        "last_seen_links": row.last_seen_links,
        "last_checked_at": row.last_checked_at.isoformat() if row.last_checked_at else None,
    }
