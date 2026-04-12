from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from flask import current_app

from app.services.google_credentials import google_credentials_status, require_google_credentials
from app.services.provider_errors import ProviderError


@dataclass(frozen=True)
class ProviderStatus:
    ok: bool
    code: str | None = None
    message: str | None = None
    detail: dict | None = None

    def as_dict(self) -> dict:
        if self.ok:
            return {"ok": True}
        payload = {"ok": False, "code": self.code, "message": self.message}
        if self.detail:
            payload["detail"] = self.detail
        return payload


class GoogleLiveProviderService:
    """
    Prepares server-side Google provider orchestration without leaking secrets.

    This service intentionally does NOT implement live stream provisioning yet.
    It only:
    - validates runtime configuration
    - validates server-side credential file availability
    - exposes safe status/error codes for UI/API
    """

    provider_name = "google"

    def status(self) -> dict[str, Any]:
        cfg_status = google_credentials_status()

        # Never attempt provider initialization if the credentials are missing/not configured.
        try:
            require_google_credentials()
        except ProviderError as exc:
            return {
                "provider": self.provider_name,
                "ready": False,
                "error": exc.as_dict(),
                "config": {
                    "configured": cfg_status["configured"],
                    "missing_fields": cfg_status["missing_fields"],
                    "credentials_file_present": cfg_status["credentials_file_present"],
                    "project_id": cfg_status["project_id"],
                    "location": cfg_status["location"],
                    "location_valid": cfg_status.get("location_valid", False),
                    "location_error": cfg_status.get("location_error"),
                    "output_bucket": cfg_status["output_bucket"],
                    "output_bucket_valid": cfg_status.get("output_bucket_valid", False),
                    "output_bucket_error": cfg_status.get("output_bucket_error"),
                    "service_account_email": cfg_status["service_account_email"],
                },
            }

        # If credentials are present, we still may not be ready until the provider adapter is implemented.
        return {
            "provider": self.provider_name,
            "ready": False,
            "error": ProviderError(
                "provider_not_ready",
                "Google provider is configured, but orchestration is not implemented yet.",
            ).as_dict(),
            "config": {
                "configured": True,
                "credentials_file_present": True,
                "project_id": cfg_status["project_id"],
                "location": cfg_status["location"],
                "location_valid": cfg_status.get("location_valid", False),
                "output_bucket": cfg_status["output_bucket"],
                "output_bucket_valid": cfg_status.get("output_bucket_valid", False),
                "service_account_email": cfg_status["service_account_email"],
            },
        }


google_live_provider_service = GoogleLiveProviderService()
