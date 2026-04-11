import unittest
from unittest.mock import patch

from app.plugins.base import BasePlugin
from app.plugins.registry import get_enabled_plugins, get_plugins, run_plugins


class DisabledPlugin(BasePlugin):
    name = "disabled"
    enabled = False

    def run(self, context: dict) -> dict:
        return {"success": True, "data": {"should_not_run": True}}


class WorkingPlugin(BasePlugin):
    name = "working"

    def run(self, context: dict) -> dict:
        return {"success": True, "data": {"value": context.get("username")}}


class FailingPlugin(BasePlugin):
    name = "failing"

    def run(self, context: dict) -> dict:
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

    @patch("app.plugins.registry.PLUGIN_CLASSES", (DisabledPlugin, WorkingPlugin))
    def test_run_plugins_marks_disabled_plugins_without_running_them(self):
        results = run_plugins({"username": "shadowseek"})

        self.assertEqual(results["disabled"]["enabled"], False)
        self.assertEqual(results["disabled"]["duration_ms"], 0)
        self.assertEqual(results["disabled"]["data"], {})
        self.assertEqual(results["disabled"]["errors"], [])
        self.assertTrue(results["working"]["enabled"])

    @patch("app.plugins.registry.PLUGIN_CLASSES", (WorkingPlugin, FailingPlugin))
    def test_run_plugins_isolates_plugin_errors(self):
        results = run_plugins({"username": "shadowseek"})

        self.assertEqual(results["working"]["data"], {"value": "shadowseek"})
        self.assertTrue(results["working"]["success"])
        self.assertFalse(results["failing"]["success"])
        self.assertTrue(results["failing"]["enabled"])
        self.assertEqual(results["failing"]["data"], {})
        self.assertEqual(results["failing"]["errors"], ["Plugin execution failed."])

    @patch("app.plugins.registry.PLUGIN_CLASSES", (WorkingPlugin,))
    def test_run_plugins_includes_duration_ms(self):
        results = run_plugins({"username": "shadowseek"})

        self.assertIn("duration_ms", results["working"])
        self.assertIsInstance(results["working"]["duration_ms"], int)

    @patch("app.plugins.registry.PLUGIN_CLASSES", (WorkingPlugin,))
    def test_run_plugins_with_empty_input_does_not_crash(self):
        results = run_plugins({})

        self.assertEqual(results["working"]["data"], {"value": None})
        self.assertEqual(results["working"]["errors"], [])


if __name__ == "__main__":
    unittest.main()
