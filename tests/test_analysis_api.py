import tempfile
import unittest
from unittest.mock import patch

from app import create_app
from app.services.deepsearch import run_deepsearch
from app.services.screenshot_engine import (
    capture_profile_screenshot,
    is_valid_capture_url,
    sanitize_filename,
)


class AnalysisApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        test_config = type(
            "AnalysisTestConfig",
            (),
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                "WTF_CSRF_ENABLED": False,
                "SESSION_COOKIE_SECURE": False,
                "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
                "SEARCH_REQUEST_TIMEOUT": 0.1,
                "SEARCH_MAX_WORKERS": 1,
                "REVERSE_IMAGE_MAX_AGE": 3600,
                "PUBLIC_BASE_URL": "https://shadowseek.example",
                "UPLOAD_DIRECTORY": self.temp_directory.name,
                "SERPER_API_KEY": None,
                "OPENAI_API_KEY": None,
                "OPENAI_MAX_RERANK_CANDIDATES": 12,
            },
        )
        self.app = create_app(test_config)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_directory.cleanup()

    def test_analysis_routes_require_json(self):
        response = self.client.post("/search/deepsearch", data="not-json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(response.get_json()["error"], "JSON body required.")

    def test_screenshot_route_validates_url(self):
        response = self.client.post("/search/screenshot", json={"slug": "test"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Missing url.")

    @patch("app.services.screenshot_engine.resolve_hostname_ips", return_value=["127.0.0.1"])
    def test_screenshot_route_blocks_internal_url(self, _resolve_ips):
        response = self.client.post(
            "/search/screenshot",
            json={"url": "http://example.com/private"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Target host is not allowed.")

    @patch("app.routes.analysis.compare_uploaded_against_gallery", return_value={"matches": []})
    def test_image_similarity_route_rejects_invalid_gallery_type(self, _compare):
        response = self.client.post(
            "/search/image-similarity",
            json={"reference_image": "/tmp/a.png", "gallery": "not-a-list"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["error"], "Missing reference_image or gallery.")

    @patch("app.routes.analysis.run_deepsearch", return_value={"similarity": {"matches": []}})
    def test_deepsearch_route_returns_json_payload(self, mocked_run):
        response = self.client.post("/search/deepsearch", json={"base_username": "shadowseek"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["success"])
        mocked_run.assert_called_once()

    def test_deepsearch_route_empty_payload_returns_stable_shape(self):
        response = self.client.post("/search/deepsearch", json={})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()["data"]
        self.assertEqual(payload["similarity"], {"matches": []})
        self.assertEqual(payload["screenshots"], [])
        self.assertEqual(payload["image_similarity"], {"matches": []})
        self.assertEqual(payload["risk_score"], {"score": 0, "level": "low", "factors": []})
        self.assertEqual(payload["usernames"], [])
        self.assertEqual(payload["profiles"], [])
        self.assertEqual(payload["reverse_image"], {})

    @patch("app.routes.analysis.run_deepsearch", side_effect=RuntimeError("boom"))
    def test_analysis_route_unexpected_error_returns_json(self, _mocked_run):
        response = self.client.post("/search/deepsearch", json={"base_username": "shadowseek"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "Internal server error"},
        )


class DeepSearchServiceTestCase(unittest.TestCase):
    @patch("app.services.deepsearch.capture_profile_screenshot", side_effect=RuntimeError("boom"))
    @patch("app.services.deepsearch.compare_uploaded_against_gallery", side_effect=RuntimeError("boom"))
    @patch("app.services.deepsearch.calculate_osint_risk", side_effect=RuntimeError("boom"))
    @patch("app.services.deepsearch.find_similar_usernames", side_effect=RuntimeError("boom"))
    def test_run_deepsearch_isolates_submodule_failures(
        self,
        _find_similar,
        _calculate_risk,
        _compare_images,
        _capture_screenshot,
    ):
        result = run_deepsearch(
            {
                "base_username": "shadowseek",
                "candidates": ["shadowseek1"],
                "profile_urls": ["https://example.com/user"],
                "reference_image": "ref.png",
                "gallery": ["a.png"],
                "riskdata": {"has_real_name": True},
                "profiles": {"unexpected": True},
            }
        )

        self.assertEqual(result["similarity"], {"matches": []})
        self.assertEqual(result["screenshots"], [])
        self.assertEqual(result["image_similarity"], {"matches": []})
        self.assertEqual(result["risk_score"]["score"], 0)
        self.assertEqual(result["profiles"], [])


class ScreenshotEngineTestCase(unittest.TestCase):
    def test_url_validation_accepts_only_http_https(self):
        with patch("app.services.screenshot_engine.resolve_hostname_ips", return_value=["93.184.216.34"]):
            self.assertEqual(is_valid_capture_url("https://example.com/profile"), (True, None))
        self.assertEqual(is_valid_capture_url("file:///tmp/test"), (False, "Invalid or missing URL."))
        self.assertEqual(
            is_valid_capture_url("javascript:alert(1)"),
            (False, "Invalid or missing URL."),
        )

    @patch("app.services.screenshot_engine.resolve_hostname_ips", return_value=["127.0.0.1"])
    def test_url_validation_blocks_private_targets(self, _resolve_ips):
        self.assertEqual(
            is_valid_capture_url("http://shadowseek.test/internal"),
            (False, "Target host is not allowed."),
        )

    def test_sanitize_filename_never_returns_empty(self):
        self.assertEqual(sanitize_filename("../../../"), "screenshot")

    @patch("app.services.screenshot_engine.PLAYWRIGHT_AVAILABLE", False)
    def test_capture_profile_screenshot_returns_structured_error_without_playwright(self):
        result = capture_profile_screenshot("https://example.com/profile")

        self.assertFalse(result["success"])
        self.assertIn("Playwright", result["message"])


if __name__ == "__main__":
    unittest.main()
