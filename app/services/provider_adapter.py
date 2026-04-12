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

    def stop_stream(self, provider_channel_id: str) -> dict[str, Any]:
        raise NotImplementedError


class GoogleLiveProviderAdapter(ProviderAdapter):
    provider_name = "google"

    def create_stream(self, stream_meta: dict[str, Any]) -> dict[str, Any]:
        try:
            input_info = google_live_provider_service.create_input_endpoint(stream_meta["title"])
            channel_info = google_live_provider_service.create_channel(
                stream_meta["title"],
                input_info["input_id"],
            )
            return {
                "provider": self.provider_name,
                "provider_input_id": input_info["input_id"],
                "provider_channel_id": channel_info["channel_id"],
                "ingest_url": input_info["ingest_url"],
                "playback_url": channel_info["playback_url"],
                "stream_key": input_info.get("stream_key"),
                "provider_status": "provisioning",
            }
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("provider_not_ready", f"Google stream creation failed: {exc}")

    def get_stream_status(self, provider_channel_id: str) -> dict[str, Any]:
        try:
            return google_live_provider_service.get_channel_status(provider_channel_id)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("provider_not_ready", f"Google get_stream_status failed: {exc}")

    def stop_stream(self, provider_channel_id: str) -> dict[str, Any]:
        try:
            return google_live_provider_service.stop_channel(provider_channel_id)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("provider_not_ready", f"Google stop_stream failed: {exc}")


PROVIDER_ADAPTERS: dict[str, ProviderAdapter] = {
    "google": GoogleLiveProviderAdapter(),
}


def get_provider_adapter(provider: str) -> ProviderAdapter | None:
    return PROVIDER_ADAPTERS.get((provider or "").strip().lower())