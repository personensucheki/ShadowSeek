from app.plugins.base import BasePlugin
from app.plugins.modules import (
    DomainOsintPlugin,
    RiskScorePlugin,
    UsernamePatternsPlugin,
    UsernameSimilarityPlugin,
)


PLUGIN_CLASSES = (
    UsernameSimilarityPlugin,
    RiskScorePlugin,
    UsernamePatternsPlugin,
    DomainOsintPlugin,
)


def get_plugins():
    return [plugin_class() for plugin_class in PLUGIN_CLASSES]


def get_enabled_plugins():
    return [plugin for plugin in get_plugins() if getattr(plugin, "enabled", False)]


def run_plugins(data: dict) -> dict:
    results = {}
    for plugin in get_enabled_plugins():
        try:
            result = plugin.run(data or {})
            if not isinstance(result, dict):
                result = {"success": False, "error": "Plugin returned invalid payload."}
        except Exception:
            result = plugin.error_result()
        results[plugin.name] = result
    return results
