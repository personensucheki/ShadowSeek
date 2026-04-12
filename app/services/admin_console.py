from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from flask import current_app


DEFAULT_ADMIN_CONSOLE_STATE = {
    "settings": {
        "maintenance_mode": False,
        "registrations_open": True,
        "deepsearch_enabled": True,
        "billing_enforced": True,
        "manual_review_required": False,
        "priority_alerts": True,
    },
    "maintenance_notice": {
        "title": "",
        "body": "",
        "severity": "info",
        "target": "all",
        "updated_at": None,
    },
    "discounts": [],
}


def _state_file() -> Path:
    return Path(current_app.instance_path) / "admin_console_state.json"


def load_admin_console_state() -> dict:
    state = json.loads(json.dumps(DEFAULT_ADMIN_CONSOLE_STATE))
    state_file = _state_file()
    if not state_file.exists():
        return state

    try:
        with state_file.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
    except (OSError, json.JSONDecodeError):
        current_app.logger.warning("admin_console_state_unreadable path=%s", state_file)
        return state

    if isinstance(loaded, dict):
        state["settings"].update(loaded.get("settings") or {})
        state["maintenance_notice"].update(loaded.get("maintenance_notice") or {})
        if isinstance(loaded.get("discounts"), list):
            state["discounts"] = loaded["discounts"][:12]
    return state


def save_admin_console_state(state: dict) -> None:
    state_file = _state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, ensure_ascii=True, indent=2)


def update_console_settings(form_data) -> dict:
    state = load_admin_console_state()
    state["settings"] = {
        "maintenance_mode": form_data.get("maintenance_mode") == "on",
        "registrations_open": form_data.get("registrations_open") == "on",
        "deepsearch_enabled": form_data.get("deepsearch_enabled") == "on",
        "billing_enforced": form_data.get("billing_enforced") == "on",
        "manual_review_required": form_data.get("manual_review_required") == "on",
        "priority_alerts": form_data.get("priority_alerts") == "on",
    }
    save_admin_console_state(state)
    return state


def update_maintenance_notice(form_data, actor_username: str) -> dict:
    state = load_admin_console_state()
    state["maintenance_notice"] = {
        "title": (form_data.get("title") or "").strip()[:120],
        "body": (form_data.get("body") or "").strip()[:1000],
        "severity": (form_data.get("severity") or "info").strip()[:16],
        "target": (form_data.get("target") or "all").strip()[:32],
        "updated_at": datetime.utcnow().isoformat(timespec="seconds"),
        "updated_by": actor_username,
    }
    save_admin_console_state(state)
    return state


def add_discount_entry(form_data, actor_username: str) -> dict:
    state = load_admin_console_state()
    code = (form_data.get("code") or "").strip().upper()[:32]
    percent = int(form_data.get("percent") or 0)
    target_user = (form_data.get("target_user") or "").strip()[:80]
    expires_at = (form_data.get("expires_at") or "").strip()[:32]

    if not code:
        raise ValueError("Rabattcode fehlt.")
    if percent < 1 or percent > 100:
        raise ValueError("Rabatt muss zwischen 1 und 100 Prozent liegen.")

    state["discounts"].insert(
        0,
        {
            "code": code,
            "percent": percent,
            "target_user": target_user or "alle aktiven Nutzer",
            "expires_at": expires_at or "offen",
            "created_at": datetime.utcnow().isoformat(timespec="seconds"),
            "created_by": actor_username,
        },
    )
    state["discounts"] = state["discounts"][:12]
    save_admin_console_state(state)
    return state
