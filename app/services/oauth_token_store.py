from __future__ import annotations

from datetime import datetime, timedelta

import requests
from flask import current_app

from ..extensions import db
from ..models.oauth_token import OAuthToken
from .token_crypto import decrypt_text, encrypt_text


def upsert_token(
    *,
    user_id: int,
    provider: str,
    access_token: str,
    refresh_token: str | None,
    expires_in: int | None,
    scope: str | None = None,
    token_type: str | None = None,
) -> OAuthToken:
    provider = provider.strip().lower()
    if not provider:
        raise ValueError("provider missing")
    if not access_token:
        raise ValueError("access_token missing")

    expires_at = None
    if expires_in:
        # Small safety buffer
        expires_at = datetime.utcnow() + timedelta(seconds=max(0, int(expires_in) - 15))

    row = OAuthToken.query.filter_by(user_id=user_id, provider=provider).first()
    if not row:
        row = OAuthToken(user_id=user_id, provider=provider, access_token_enc="")  # placeholder
        db.session.add(row)

    row.access_token_enc = encrypt_text(access_token) or ""
    row.refresh_token_enc = encrypt_text(refresh_token) if refresh_token else None
    row.expires_at = expires_at
    row.scope = scope
    row.token_type = token_type
    db.session.commit()
    return row


def get_access_token(user_id: int, provider: str) -> str | None:
    provider = provider.strip().lower()
    row = OAuthToken.query.filter_by(user_id=user_id, provider=provider).first()
    if not row:
        return None
    if row.expires_at and row.expires_at <= datetime.utcnow():
        return None
    return decrypt_text(row.access_token_enc)


def get_valid_access_token(user_id: int, provider: str) -> str | None:
    """
    Returns a non-expired access token. If expired, tries to refresh automatically
    when a refresh_token is available.
    """
    provider = provider.strip().lower()
    row = OAuthToken.query.filter_by(user_id=user_id, provider=provider).first()
    if not row:
        return None

    access_token = decrypt_text(row.access_token_enc)
    refresh_token = decrypt_text(row.refresh_token_enc) if row.refresh_token_enc else None

    if row.expires_at and row.expires_at <= datetime.utcnow():
        if not refresh_token:
            return None
        refreshed = _refresh_token(provider, refresh_token)
        if not refreshed:
            return None
        access_token = refreshed.get("access_token")
        if not access_token:
            return None
        row.access_token_enc = encrypt_text(access_token) or ""
        row.token_type = refreshed.get("token_type") or row.token_type
        expires_in = refreshed.get("expires_in")
        if expires_in:
            row.expires_at = datetime.utcnow() + timedelta(seconds=max(0, int(expires_in) - 15))
        db.session.commit()

    return access_token


def _refresh_token(provider: str, refresh_token: str) -> dict | None:
    try:
        if provider == "google":
            client_id = current_app.config.get("GOOGLE_OAUTH_CLIENT_ID")
            client_secret = current_app.config.get("GOOGLE_OAUTH_CLIENT_SECRET")
            if not client_id or not client_secret:
                return None
            resp = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                timeout=10,
            )
            if resp.status_code >= 400:
                return None
            return resp.json()

        if provider == "twitch":
            client_id = current_app.config.get("TWITCH_CLIENT_ID")
            client_secret = current_app.config.get("TWITCH_CLIENT_SECRET")
            if not client_id or not client_secret:
                return None
            resp = requests.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                timeout=10,
            )
            if resp.status_code >= 400:
                return None
            return resp.json()
    except requests.RequestException:
        return None

    return None


def is_connected(user_id: int, provider: str) -> bool:
    token = get_valid_access_token(user_id, provider)
    return bool(token)


def require_user_session_user_id(session: dict) -> int:
    user_id = session.get("user_id")
    if not user_id:
        raise PermissionError("Nicht eingeloggt.")
    return int(user_id)
