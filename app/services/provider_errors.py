from __future__ import annotations

from dataclasses import dataclass


# Canonical provider error codes for UI/API.
PROVIDER_ERROR_CODES = {
    "credentials_missing",
    "invalid_credentials_format",
    "validation_error",
    "provider_auth_failed",
    "provider_permission_denied",
    "provider_not_ready",
    "provider_not_configured",
}


@dataclass(frozen=True)
class ProviderError(Exception):
    code: str
    message: str
    detail: dict | None = None

    def __post_init__(self) -> None:
        if self.code not in PROVIDER_ERROR_CODES:
            raise ValueError(f"Unknown provider error code: {self.code}")

    def as_dict(self) -> dict:
        payload = {"code": self.code, "message": self.message}
        if self.detail:
            payload["detail"] = self.detail
        return payload
