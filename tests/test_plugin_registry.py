import unittest
from unittest.mock import patch

from app.plugins.base import BasePlugin
from app.plugins.registry import get_enabled_plugins, get_plugins, run_plugins


class DisabledPlugin(BasePlugin):
    name = "disabled"
    enabled = False

    def run(self, data: dict) -> dict:
        return {"success": True}


class WorkingPlugin(BasePlugin):
    name = "working"

    def run(self, data: dict) -> dict:
        return {"success": True, "value": data.get("value")}


class FailingPlugin(BasePlugin):
    name = "failing"

    def run(self, data: dict) -> dict:
        raise RuntimeError("boom")


class PluginRegistryTestCase(unittest.TestCase):
    def test_get_plugins_returns_instances(self):
        plugins = get_plugins()

        self.assertTrue(plugins)
        self.assertTrue(all(hasattr(plugin, "run") for plugin in plugins))

    @patch("app.plugins.registry.PLUGIN_CLASSES", (DisabledPlugin, WorkingPlugin))
    def test_get_enabled_plugins_skips_disabled_plugins(self):
        plugins = get_enabled_plugins()

        self.assertEqual([plugin.name for plugin in plugins], ["working"])

    @patch("app.plugins.registry.PLUGIN_CLASSES", (WorkingPlugin, FailingPlugin))
    def test_run_plugins_isolates_plugin_errors(self):
        results = run_plugins({"value": 7})

        self.assertEqual(results["working"], {"success": True, "value": 7})
        self.assertEqual(
            results["failing"],
            {"success": False, "error": "Plugin execution failed."},
        )


if __name__ == "__main__":
    unittest.main()
