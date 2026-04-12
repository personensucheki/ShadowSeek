from __future__ import annotations

import base64
import hashlib
import os
import secrets
from urllib.parse import urlencode

import requests
from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for

from ..services.oauth_token_store import require_user_session_user_id, upsert_token


oauth_bp = Blueprint("oauth_connect", __name__, url_prefix="/auth")


def _wants_json() -> bool:
    if request.is_json:
        return True
    accept = request.headers.get("Accept", "")
    return "application/json" in (accept or "").lower()


def _callback_url(provider: str) -> str:
    # Local default: http://127.0.0.1:5000/auth/callback/<provider>
    return url_for("oauth_connect.oauth_callback", provider=provider, _external=True)


@oauth_bp.route("/connect/<provider>", methods=["GET"])
def connect(provider: str):
    provider = (provider or "").strip().lower()
    user_id = require_user_session_user_id(session)

    if provider == "twitch":
        client_id = current_app.config.get("TWITCH_CLIENT_ID")
        if not client_id:
            return jsonify(success=False, error="TWITCH_CLIENT_ID fehlt."), 400

        state = secrets.token_urlsafe(24)
        session["oauth_state:twitch"] = state
        session["oauth_user:twitch"] = user_id

        params = {
            "client_id": client_id,
            "redirect_uri": _callback_url("twitch"),
            "response_type": "code",
            "scope": "user:read:email",  # minimal; erweitern wir später
            "state": state,
            "force_verify": "true",
        }
        return redirect("https://id.twitch.tv/oauth2/authorize?" + urlencode(params))

    if provider in {"google", "youtube"}:
        client_id = current_app.config.get("GOOGLE_OAUTH_CLIENT_ID")
        if not client_id:
            return jsonify(success=False, error="GOOGLE_OAUTH_CLIENT_ID fehlt."), 400

        state = secrets.token_urlsafe(24)
        session["oauth_state:google"] = state
        session["oauth_user:google"] = user_id

        # PKCE (recommended)
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest()).rstrip(b"=").decode("utf-8")
        session["oauth_pkce:google"] = verifier

        params = {
            "client_id": client_id,
            "redirect_uri": _callback_url("google"),
            "response_type": "code",
            "scope": (
                "openid email profile "
                "https://www.googleapis.com/auth/youtube.readonly "
                "https://www.googleapis.com/auth/yt-analytics.readonly"
            ),
            "state": state,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        return redirect("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))

    return jsonify(success=False, error=f"Provider '{provider}' wird noch nicht unterstützt."), 400


@oauth_bp.route("/callback/<provider>", methods=["GET"])
def oauth_callback(provider: str):
    provider = (provider or "").strip().lower()
    code = request.args.get("code", "")
    state = request.args.get("state", "")
    error = request.args.get("error", "")

    if error:
        return jsonify(success=False, error=error), 400
    if not code:
        return jsonify(success=False, error="Kein OAuth code erhalten."), 400

    if provider == "twitch":
        if state != session.get("oauth_state:twitch"):
            return jsonify(success=False, error="OAuth state mismatch."), 400
        user_id = session.get("oauth_user:twitch")
        if not user_id:
            return jsonify(success=False, error="Session abgelaufen."), 400

        client_id = current_app.config.get("TWITCH_CLIENT_ID")
        client_secret = current_app.config.get("TWITCH_CLIENT_SECRET")
        if not client_id or not client_secret:
            return jsonify(success=False, error="Twitch OAuth nicht konfiguriert."), 400

        token_res = requests.post(
            "https://id.twitch.tv/oauth2/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": _callback_url("twitch"),
            },
            timeout=10,
        )
        if token_res.status_code >= 400:
            return jsonify(success=False, error="Twitch Token Exchange fehlgeschlagen."), 400
        payload = token_res.json()
        upsert_token(
            user_id=int(user_id),
            provider="twitch",
            access_token=payload.get("access_token") or "",
            refresh_token=payload.get("refresh_token"),
            expires_in=payload.get("expires_in"),
            scope=" ".join(payload.get("scope") or []),
            token_type=payload.get("token_type"),
        )

        # cleanup
        session.pop("oauth_state:twitch", None)
        session.pop("oauth_user:twitch", None)
        return redirect(url_for("dashboard.dashboard"))

    if provider in {"google", "youtube"}:
        if state != session.get("oauth_state:google"):
            return jsonify(success=False, error="OAuth state mismatch."), 400
        user_id = session.get("oauth_user:google")
        verifier = session.get("oauth_pkce:google")
        if not user_id or not verifier:
            return jsonify(success=False, error="Session abgelaufen."), 400

        client_id = current_app.config.get("GOOGLE_OAUTH_CLIENT_ID")
        client_secret = current_app.config.get("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_id or not client_secret:
            return jsonify(success=False, error="Google OAuth nicht konfiguriert."), 400

        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": _callback_url("google"),
                "code_verifier": verifier,
            },
            timeout=10,
        )
        if token_res.status_code >= 400:
            return jsonify(success=False, error="Google Token Exchange fehlgeschlagen."), 400
        payload = token_res.json()
        upsert_token(
            user_id=int(user_id),
            provider="google",
            access_token=payload.get("access_token") or "",
            refresh_token=payload.get("refresh_token"),
            expires_in=payload.get("expires_in"),
            scope=payload.get("scope"),
            token_type=payload.get("token_type"),
        )

        session.pop("oauth_state:google", None)
        session.pop("oauth_user:google", None)
        session.pop("oauth_pkce:google", None)
        return redirect(url_for("dashboard.dashboard"))

    return jsonify(success=False, error=f"Provider '{provider}' callback nicht unterstützt."), 400


@oauth_bp.route("/connections", methods=["GET"])
def connections():
    # Simple endpoint for UI to show which integrations are connected.
    try:
        user_id = require_user_session_user_id(session)
    except PermissionError as exc:
        return jsonify(success=False, error=str(exc)), 401

    from ..services.oauth_token_store import is_connected

    return jsonify(
        success=True,
        connections={
            "twitch": is_connected(user_id, "twitch"),
            "google": is_connected(user_id, "google"),
        },
    )
