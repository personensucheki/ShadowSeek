import unittest
from unittest.mock import patch

from app.services.deepsearch import run_deepsearch


class DeepSearchPluginsTestCase(unittest.TestCase):
    def test_deepsearch_returns_plugin_results_with_stable_keys(self):
        result = run_deepsearch(
            {
                "base_username": "shadowseek",
                "candidates": ["shadowseek2024", "shadow_seek"],
                "riskdata": {"has_real_name": True},
                "website": "https://shadowseek.example",
                "email": "ops@shadowseek.example",
            }
        )

        self.assertIn("plugin_results", result)
        self.assertIn("username_similarity", result["plugin_results"])
        self.assertIn("risk_score", result["plugin_results"])
        self.assertIn("username_patterns", result["plugin_results"])
        self.assertIn("domain_osint", result["plugin_results"])
        self.assertTrue(result["plugin_results"]["username_similarity"]["success"])
        self.assertIn("matches", result["plugin_results"]["username_similarity"])
        self.assertIn("score", result["plugin_results"]["risk_score"])
        self.assertIn("style", result["plugin_results"]["username_patterns"])
        self.assertIn("domains", result["plugin_results"]["domain_osint"])

    @patch("app.services.deepsearch.run_plugins", return_value={"broken": {"success": False, "error": "Plugin execution failed."}})
    def test_deepsearch_survives_plugin_failures(self, mocked_run_plugins):
        result = run_deepsearch({"base_username": "shadowseek"})

        self.assertEqual(
            result["plugin_results"],
            {"broken": {"success": False, "error": "Plugin execution failed."}},
        )
        mocked_run_plugins.assert_called_once()

    def test_deepsearch_empty_input_keeps_plugin_results_stable(self):
        result = run_deepsearch({})

        self.assertEqual(result["similarity"], {"matches": []})
        self.assertEqual(result["screenshots"], [])
        self.assertEqual(result["image_similarity"], {"matches": []})
        self.assertEqual(result["risk_score"], {"score": 0, "level": "low", "factors": []})
        self.assertIn("plugin_results", result)
        self.assertEqual(
            sorted(result["plugin_results"].keys()),
            ["domain_osint", "risk_score", "username_patterns", "username_similarity"],
        )


if __name__ == "__main__":
    unittest.main()
