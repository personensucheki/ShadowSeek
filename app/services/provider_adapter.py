"""
ProviderAdapter-Konzept für externe Live-Provider (Google, Mux, etc.).

Security principles:
- Credentials are server-side only and must never be committed or exposed to the frontend.
- Do not attempt provider initialization if credentials/config are missing.
- Expose stable, typed error codes for UI/API.
"""

from __future__ import annotations

from typing import Any

from app.services.google_live_provider_service import google_live_provider_service
from app.services.provider_errors import ProviderError


class ProviderAdapter:
    def create_stream(self, stream_meta: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def get_stream_status(self, provider_input_id: str) -> dict[str, Any]:
        raise NotImplementedError


class GoogleLiveProviderAdapter(ProviderAdapter):
    provider_name = "google"

    def create_stream(self, stream_meta: dict[str, Any]) -> dict[str, Any]:
        # Not implemented yet; return typed errors via exception so callers can map to API.
        status = google_live_provider_service.status()
        error = status.get("error") or {}
        raise ProviderError(
            error.get("code") or "provider_not_ready",
            error.get("message") or "Google provider not ready.",
            detail=error.get("detail"),
        )

    def get_stream_status(self, provider_input_id: str) -> dict[str, Any]:
        status = google_live_provider_service.status()
        error = status.get("error") or {}
        raise ProviderError(
            error.get("code") or "provider_not_ready",
            error.get("message") or "Google provider not ready.",
            detail=error.get("detail"),
        )


PROVIDER_ADAPTERS: dict[str, ProviderAdapter] = {
    "google": GoogleLiveProviderAdapter(),
}


def get_provider_adapter(provider: str) -> ProviderAdapter | None:
    return PROVIDER_ADAPTERS.get((provider or "").strip().lower())

