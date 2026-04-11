import unittest
from unittest.mock import patch

from app.services.deepsearch import run_deepsearch


class DeepSearchPluginsTestCase(unittest.TestCase):
    def test_deepsearch_returns_plugin_results_with_stable_keys(self):
        result = run_deepsearch(
            {
                "base_username": "shadowseek",
                "real_name": "Shadow Seek",
                "age": 28,
                "postal_code": "10115",
                "reference_image": "/tmp/shadowseek.png",
            }
        )

        self.assertIn("plugin_results", result)
        self.assertEqual(
            list(result["plugin_results"].keys()),
            ["username_similarity", "username_patterns", "domain_osint", "risk_score"],
        )

        for plugin_result in result["plugin_results"].values():
            self.assertIn("success", plugin_result)
            self.assertIn("enabled", plugin_result)
            self.assertIn("duration_ms", plugin_result)
            self.assertIn("data", plugin_result)
            self.assertIn("errors", plugin_result)
            self.assertIsInstance(plugin_result["data"], dict)
            self.assertIsInstance(plugin_result["errors"], list)

        self.assertIn("matches", result["plugin_results"]["username_similarity"]["data"])
        self.assertIn("score", result["plugin_results"]["risk_score"]["data"])
        self.assertIn("style", result["plugin_results"]["username_patterns"]["data"])
        self.assertIn("domains", result["plugin_results"]["domain_osint"]["data"])

    @patch(
        "app.services.deepsearch.run_plugins",
        return_value={
            "broken": {
                "success": False,
                "enabled": True,
                "duration_ms": 1,
                "data": {},
                "errors": ["Plugin execution failed."],
            }
        },
    )
    def test_deepsearch_survives_plugin_failures(self, mocked_run_plugins):
        result = run_deepsearch({"base_username": "shadowseek"})

        self.assertEqual(
            result["plugin_results"],
            {
                "broken": {
                    "success": False,
                    "enabled": True,
                    "duration_ms": 1,
                    "data": {},
                    "errors": ["Plugin execution failed."],
                }
            },
        )
        mocked_run_plugins.assert_called_once()

    def test_deepsearch_empty_input_keeps_plugin_results_stable(self):
        result = run_deepsearch({})

        self.assertEqual(result["similarity"], {"matches": []})
        self.assertEqual(result["screenshots"], [])
        self.assertEqual(result["image_similarity"], {"matches": []})
        self.assertEqual(result["risk_score"], {"score": 0, "level": "low", "factors": []})
        self.assertEqual(result["images"], [])
        self.assertIn("plugin_results", result)
        self.assertEqual(
            sorted(result["plugin_results"].keys()),
            ["domain_osint", "risk_score", "username_patterns", "username_similarity"],
        )


if __name__ == "__main__":
    unittest.main()
