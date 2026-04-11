from __future__ import annotations

from datetime import datetime

from app.models import EinnahmeInfo


DEFAULT_CONFIDENCE = 0.7


def event_from_legacy_row(entry: dict) -> dict:
    """Normalize legacy collector rows to the unified RevenueEvent shape."""
    typ = (entry.get("typ") or "unknown").strip().lower()
    platform = typ.split("_", 1)[0] if "_" in typ else typ
    username = (entry.get("quelle") or "unknown").strip()
    captured_at = entry.get("zeitpunkt") or datetime.utcnow()

    return {
        "platform": platform or "unknown",
        "username": username or "unknown",
        "display_name": (entry.get("display_name") or username or "unknown").strip(),
        "estimated_revenue": float(entry.get("betrag") or 0.0),
        "currency": (entry.get("waehrung") or "EUR").strip().upper(),
        "captured_at": captured_at,
        "source": (entry.get("source") or "scraper").strip().lower(),
        "confidence": float(entry.get("confidence") or DEFAULT_CONFIDENCE),
        "typ": typ,
        "details": entry.get("details"),
    }


def serialize_revenue_event(entry: EinnahmeInfo) -> dict:
    return {
        "id": entry.id,
        "platform": entry.platform,
        "username": entry.username,
        "display_name": entry.display_name,
        "estimated_revenue": entry.estimated_revenue,
        "currency": entry.currency,
        "captured_at": entry.captured_at.isoformat(),
        "source": entry.source,
        "confidence": entry.confidence,
    }
