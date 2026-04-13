from __future__ import annotations

import os


def optional_integration_enabled(env_key: str) -> bool:
    return bool((os.environ.get(env_key) or "").strip())


def require_optional_integration(env_key: str, feature_name: str) -> tuple[bool, str | None]:
    if optional_integration_enabled(env_key):
        return True, None
    return False, f"{feature_name} is disabled because {env_key} is not configured."


def feature_flag_enabled(env_key: str, default: bool = False) -> bool:
    raw = (os.environ.get(env_key) or "").strip().lower()
    if not raw:
        return bool(default)
    return raw in {"1", "true", "yes", "on"}
