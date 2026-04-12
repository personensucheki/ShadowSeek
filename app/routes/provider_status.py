from __future__ import annotations

from flask import Blueprint, jsonify

from app.services.google_live_provider_service import google_live_provider_service


provider_status_bp = Blueprint("provider_status", __name__, url_prefix="/api/providers")


@provider_status_bp.get("/status")
def provider_status():
    """
    Safe provider status endpoint.
    - No secrets returned.
    - Distinguishes missing creds/config vs. auth/permission vs. not-ready.
    """
    google_status = google_live_provider_service.status()

    # OBS/RTMP is still the production path; Google orchestration is optional.
    return jsonify(
        {
            "success": True,
            "providers": {
                "google": google_status,
            },
        }
    )

