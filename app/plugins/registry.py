from __future__ import annotations

import logging
import time
from collections import deque
from typing import Any

from app.plugins.base import BasePlugin
from app.plugins.modules import (
    DomainOsintPlugin,
    RiskScorePlugin,
    UsernamePatternsPlugin,
    UsernameSimilarityPlugin,
)


logger = logging.getLogger(__name__)

PLUGIN_SETTINGS: dict[str, bool] = {
    "username_similarity": True,
    "username_patterns": True,
    "domain_osint": True,
    "risk_score": True,
}

PLUGIN_CLASSES = (
    UsernameSimilarityPlugin,
    UsernamePatternsPlugin,
    DomainOsintPlugin,
    RiskScorePlugin,
)


def get_plugins() -> list[BasePlugin]:
    return [plugin_class() for plugin_class in PLUGIN_CLASSES]


def _resolve_enabled(
    plugin: BasePlugin,
    config_overrides: dict[str, bool] | None = None,
    runtime_overrides: dict[str, bool] | None = None,
) -> bool:
    enabled = bool(getattr(plugin, "enabled", False))
    merged_config = {**PLUGIN_SETTINGS, **(config_overrides or {})}
    if plugin.name in merged_config:
        enabled = bool(merged_config[plugin.name])
    if runtime_overrides and plugin.name in runtime_overrides:
        enabled = bool(runtime_overrides[plugin.name])
    return enabled


def _toposort_plugins(plugins: list[BasePlugin]) -> list[BasePlugin]:
    plugins_by_name = {plugin.name: plugin for plugin in plugins}
    indegree = {plugin.name: 0 for plugin in plugins}
    adjacency: dict[str, list[str]] = {plugin.name: [] for plugin in plugins}
    order_index = {plugin.name: index for index, plugin in enumerate(plugins)}

    for plugin in plugins:
        for dependency in getattr(plugin, "requires", []):
            if dependency not in plugins_by_name:
                continue
            adjacency[dependency].append(plugin.name)
            indegree[plugin.name] += 1

    queue = deque(
        sorted(
            (plugin.name for plugin in plugins if indegree[plugin.name] == 0),
            key=lambda name: order_index[name],
        )
    )
    ordered_names: list[str] = []

    while queue:
        plugin_name = queue.popleft()
        ordered_names.append(plugin_name)
        for child_name in sorted(adjacency[plugin_name], key=lambda name: order_index[name]):
            indegree[child_name] -= 1
            if indegree[child_name] == 0:
                queue.append(child_name)

    if len(ordered_names) != len(plugins):
        return sorted(plugins, key=lambda plugin: order_index[plugin.name])

    return [plugins_by_name[name] for name in ordered_names]


def get_enabled_plugins(
    config_overrides: dict[str, bool] | None = None,
    runtime_overrides: dict[str, bool] | None = None,
) -> list[BasePlugin]:
    enabled_plugins = [
        plugin
        for plugin in get_plugins()
        if _resolve_enabled(plugin, config_overrides, runtime_overrides)
    ]
    return _toposort_plugins(enabled_plugins)


def _normalize_plugin_result(
    raw_result: dict[str, Any] | None,
    *,
    enabled: bool,
    duration_ms: int,
    error_message: str | None = None,
) -> dict[str, Any]:
    payload = raw_result if isinstance(raw_result, dict) else {}
    errors = payload.get("errors")
    if not isinstance(errors, list):
        errors = []
    safe_errors = [str(error) for error in errors if error]
    if error_message:
        safe_errors.append(error_message)

    data = payload.get("data")
    if not isinstance(data, dict):
        data = {
            key: value
            for key, value in payload.items()
            if key not in {"plugin_name", "success", "enabled", "duration_ms", "data", "errors"}
        }

    return {
        "success": bool(payload.get("success", enabled and not safe_errors)),
        "enabled": bool(enabled),
        "duration_ms": int(max(duration_ms, 0)),
        "data": data if isinstance(data, dict) else {},
        "errors": safe_errors,
    }


def run_plugins(
    context: dict[str, Any] | None,
    *,
    config_overrides: dict[str, bool] | None = None,
    runtime_overrides: dict[str, bool] | None = None,
) -> dict[str, dict[str, Any]]:
    plugin_context = dict(context or {})
    results: dict[str, dict[str, Any]] = {}

    for plugin in _toposort_plugins(get_plugins()):
        enabled = _resolve_enabled(plugin, config_overrides, runtime_overrides)
        if not enabled:
            results[plugin.name] = _normalize_plugin_result(
                {},
                enabled=False,
                duration_ms=0,
            )
            continue

        execution_context = dict(plugin_context)
        execution_context["plugin_results"] = results
        start = time.perf_counter()
        try:
            raw_result = plugin.run(execution_context)
            duration_ms = int((time.perf_counter() - start) * 1000)
            results[plugin.name] = _normalize_plugin_result(
                raw_result,
                enabled=True,
                duration_ms=duration_ms,
            )
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.exception("plugin_failed", extra={"plugin": plugin.name})
            results[plugin.name] = _normalize_plugin_result(
                {},
                enabled=True,
                duration_ms=duration_ms,
                error_message="Plugin execution failed.",
            )

    return results
