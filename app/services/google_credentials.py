from __future__ import annotations

import json
import hashlib
import re
from pathlib import Path

from flask import current_app

from app.services.provider_errors import ProviderError


_BUCKET_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$")
_FORBIDDEN_BUCKET_SUBSTRINGS = ("gs://", "http://", "https://")


def validate_gcs_bucket_name(value: str) -> str:
    """
    Validates that `value` is a plain GCS bucket name (no gs:// prefix, no URL, no object path).
    Returns the trimmed bucket name when valid.
    Raises ProviderError(validation_error/provider_not_configured) otherwise.
    """
    raw = (value or "").strip()
    if not raw:
        raise ProviderError(
            "provider_not_configured",
            "Google output bucket is not configured.",
            detail={"missing_fields": ["GOOGLE_CLOUD_OUTPUT_BUCKET"]},
        )

    lowered = raw.lower()
    if any(token in lowered for token in _FORBIDDEN_BUCKET_SUBSTRINGS):
        raise ProviderError(
            "validation_error",
            "GOOGLE_CLOUD_OUTPUT_BUCKET must be a plain bucket name (no gs:// or URL).",
            detail={"value": raw},
        )
    if "/" in raw or "\\" in raw:
        raise ProviderError(
            "validation_error",
            "GOOGLE_CLOUD_OUTPUT_BUCKET must not include an object path or subdirectory.",
            detail={"value": raw},
        )
    if ":" in raw:
        raise ProviderError(
            "validation_error",
            "GOOGLE_CLOUD_OUTPUT_BUCKET must not include a scheme or port.",
            detail={"value": raw},
        )
    if not _BUCKET_NAME_PATTERN.match(raw):
        raise ProviderError(
            "validation_error",
            "GOOGLE_CLOUD_OUTPUT_BUCKET has an invalid bucket-name format.",
            detail={"value": raw},
        )
    return raw


def _normalize_credentials_path(raw: str) -> Path | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser()


def google_credentials_status() -> dict:
    """
    Returns a safe, UI-friendly status for Google credentials/config.
    Never returns secrets or credential file contents.
    """
    cfg = current_app.config
    project_id = (cfg.get("GOOGLE_CLOUD_PROJECT_ID") or "").strip()
    location = (cfg.get("GOOGLE_CLOUD_LOCATION") or "").strip()
    output_bucket = (cfg.get("GOOGLE_CLOUD_OUTPUT_BUCKET") or "").strip()
    cred_path_raw = (cfg.get("GOOGLE_APPLICATION_CREDENTIALS") or "").strip()
    sa_email = (cfg.get("GOOGLE_SERVICE_ACCOUNT_EMAIL") or "").strip()

    missing_fields = []
    if not project_id:
        missing_fields.append("GOOGLE_CLOUD_PROJECT_ID")
    if not location:
        missing_fields.append("GOOGLE_CLOUD_LOCATION")
    bucket_valid = False
    bucket_error = None
    if not output_bucket:
        missing_fields.append("GOOGLE_CLOUD_OUTPUT_BUCKET")
    else:
        try:
            validate_gcs_bucket_name(output_bucket)
            bucket_valid = True
        except ProviderError as exc:
            bucket_error = exc.as_dict()

    cred_path = _normalize_credentials_path(cred_path_raw)
    if cred_path is None:
        missing_fields.append("GOOGLE_APPLICATION_CREDENTIALS")

    file_exists = bool(cred_path and cred_path.exists() and cred_path.is_file())

    return {
        "configured": not missing_fields,
        "missing_fields": missing_fields,
        "service_account_email": sa_email or None,
        "credentials_file_present": file_exists,
        "credentials_path_hint": str(cred_path) if cred_path else None,
        "project_id": project_id or None,
        "location": location or None,
        "output_bucket": output_bucket or None,
        "output_bucket_valid": bucket_valid,
        "output_bucket_error": bucket_error,
    }


def require_google_credentials() -> Path:
    """
    Validates that server-side credentials exist and look like a service account JSON.
    Returns the credential path when valid.
    Raises ProviderError with canonical codes otherwise.
    """
    status = google_credentials_status()
    if not status["configured"]:
        raise ProviderError(
            "provider_not_configured",
            "Google provider is not configured on this server.",
            detail={"missing_fields": status["missing_fields"]},
        )

    # Validate bucket format early (no implicit conversions).
    validate_gcs_bucket_name(current_app.config.get("GOOGLE_CLOUD_OUTPUT_BUCKET") or "")

    cred_path = _normalize_credentials_path(current_app.config.get("GOOGLE_APPLICATION_CREDENTIALS") or "")
    if not cred_path:
        raise ProviderError(
            "credentials_missing",
            "Google credentials path is missing.",
            detail={"missing_fields": ["GOOGLE_APPLICATION_CREDENTIALS"]},
        )

    if not cred_path.exists() or not cred_path.is_file():
        raise ProviderError(
            "credentials_missing",
            "Google credentials file is missing on the server.",
            detail={"path": str(cred_path)},
        )

    try:
        raw = cred_path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except Exception:
        raise ProviderError(
            "invalid_credentials_format",
            "Google credentials file could not be parsed as JSON.",
            detail={"path": str(cred_path)},
        )

    if not isinstance(payload, dict) or payload.get("type") != "service_account":
        raise ProviderError(
            "invalid_credentials_format",
            "Google credentials are not a service account JSON.",
            detail={"path": str(cred_path)},
        )

    # Do not validate private_key contents; just ensure the expected keys exist.
    required_keys = ("client_email", "private_key", "project_id")
    missing = [k for k in required_keys if not payload.get(k)]
    if missing:
        raise ProviderError(
            "invalid_credentials_format",
            "Google service account JSON is missing required fields.",
            detail={"missing": missing},
        )

    # Optional: block usage of known-compromised credential files via SHA256 denylist.
    denylist_raw = (current_app.config.get("GOOGLE_COMPROMISED_CREDENTIAL_SHA256") or "").strip()
    if denylist_raw:
        denylist = {
            item.strip().lower()
            for item in denylist_raw.split(",")
            if item.strip()
        }
        file_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest().lower()
        if file_hash in denylist:
            raise ProviderError(
                "provider_permission_denied",
                "Google credentials are marked as compromised and must be rotated.",
                detail={"sha256": file_hash},
            )

    # Optional: if GOOGLE_SERVICE_ACCOUNT_EMAIL is configured, enforce it matches.
    expected_email = (current_app.config.get("GOOGLE_SERVICE_ACCOUNT_EMAIL") or "").strip()
    if expected_email and str(payload.get("client_email") or "").strip() != expected_email:
        raise ProviderError(
            "provider_permission_denied",
            "Configured service account email does not match the credential file.",
            detail={"expected": expected_email, "found": payload.get("client_email")},
        )

    return cred_path
