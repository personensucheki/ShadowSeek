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
    Orchestrates Google Live Stream API (Input, Channel, Status, Stop) using server-side credentials.
    """
    provider_name = "google"

    def __init__(self):
        import os
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT_ID")
        self.location = os.environ.get("GOOGLE_CLOUD_LOCATION")
        self.output_bucket = os.environ.get("GOOGLE_CLOUD_OUTPUT_BUCKET")
        self.credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

    def _validate_config(self):
        if not all([self.project_id, self.location, self.output_bucket, self.credentials_path]):
            raise ProviderError("provider_not_configured", "Google provider config missing.")
        require_google_credentials()

    def _client(self):
        try:
            from google.cloud.video import live_stream_v1
            return live_stream_v1.LivestreamServiceClient.from_service_account_file(self.credentials_path)
        except ImportError:
            raise ProviderError("provider_not_ready", "google-cloud-video-livestream not installed.")
        except Exception as e:
            raise ProviderError("provider_auth_failed", f"Google API client init failed: {e}")

    def create_input_endpoint(self, name: str) -> dict[str, Any]:
        self._validate_config()
        client = self._client()
        from google.cloud.video import live_stream_v1
        parent = f"projects/{self.project_id}/locations/{self.location}"
        input_id = name.lower().replace(" ", "-")
        input_obj = live_stream_v1.Input(
            type_=live_stream_v1.Input.Type.RTMP_PUSH,
            tier=live_stream_v1.Input.Tier.SD
        )
        try:
            op = client.create_input(parent=parent, input_id=input_id, input=input_obj)
            result = op.result()
            return {"input_id": result.name, "ingest_url": result.uri, "stream_key": getattr(result, "stream_key", None)}
        except Exception as e:
            code = "network_error" if "google.api_core" in str(type(e)) else "provider_not_ready"
            raise ProviderError(code, f"Failed to create input endpoint: {e}")

    def create_channel(self, name: str, input_endpoint: str) -> dict[str, Any]:
        self._validate_config()
        client = self._client()
        from google.cloud.video import live_stream_v1
        parent = f"projects/{self.project_id}/locations/{self.location}"
        channel_id = name.lower().replace(" ", "-")
        channel = live_stream_v1.Channel(
            input_attachments=[
                live_stream_v1.InputAttachment(
                    key="input0",
                    input=input_endpoint
                )
            ],
            output=live_stream_v1.Channel.Output(
                uri=f"gs://{self.output_bucket}/"
            )
        )
        try:
            op = client.create_channel(parent=parent, channel_id=channel_id, channel=channel)
            result = op.result()
            return {"channel_id": result.name, "playback_url": getattr(result.output, "uri", None)}
        except Exception as e:
            code = "network_error" if "google.api_core" in str(type(e)) else "provider_not_ready"
            raise ProviderError(code, f"Failed to create channel: {e}")

    def get_channel_status(self, channel_id: str) -> dict[str, Any]:
        self._validate_config()
        client = self._client()
        try:
            channel = client.get_channel(name=channel_id)
            return {"status": getattr(channel, "streaming_state", None), "detail": channel}
        except Exception as e:
            code = "network_error" if "google.api_core" in str(type(e)) else "provider_not_ready"
            raise ProviderError(code, f"Failed to get channel status: {e}")

    def stop_channel(self, channel_id: str) -> dict[str, Any]:
        self._validate_config()
        client = self._client()
        try:
            op = client.stop_channel(name=channel_id)
            op.result()
            return {"success": True}
        except Exception as e:
            code = "network_error" if "google.api_core" in str(type(e)) else "provider_not_ready"
            raise ProviderError(code, f"Failed to stop channel: {e}")

    def status(self) -> dict[str, Any]:
        cfg_status = google_credentials_status()
        try:
            require_google_credentials()
        except ProviderError as exc:
            return {
                "provider": self.provider_name,
                "ready": False,
                "error": exc.as_dict(),
                "config": cfg_status,
            }
        return {
            "provider": self.provider_name,
            "ready": True,
            "error": None,
            "config": cfg_status,
        }


google_live_provider_service = GoogleLiveProviderService()
