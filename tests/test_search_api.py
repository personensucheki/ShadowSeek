import importlib
import io
import os
import re
import tempfile
import unittest
from unittest.mock import patch

from app import create_app


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\x0cIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xd9\x8f\xe1"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def extract_csrf_token(html):
    match = re.search(r'name="csrf-token" content="([^"]+)"', html)
    if not match:
        raise AssertionError("CSRF token meta tag not found.")
    return match.group(1)


class SearchApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        test_config = type(
            "TestConfig",
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

    @patch("app.services.search_service.discover_profiles")
    def test_search_api_returns_expected_json(self, discover_profiles):
        discover_profiles.return_value = [
            {
                "platform": "Instagram",
                "platform_slug": "instagram",
                "category": "social",
                "username": "shadowseek",
                "profile_url": "https://www.instagram.com/shadowseek/",
                "match_score": 100,
                "verification": "confirmed",
                "match_reason": "Direkter Username",
                "http_status": 200,
            }
        ]

        response = self.client.post(
            "/api/search",
            data={
                "username": "ShadowSeek",
                "real_name": "Max Mustermann",
                "platforms": ["instagram", "reddit"],
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["query"]["username"], "shadowseek")
        self.assertLessEqual(len(payload["username_variations"]), 8)
        self.assertEqual(payload["profiles"][0]["platform"], "Instagram")

    @patch("app.services.search_service.discover_profiles", return_value=[])
    def test_image_upload_returns_signed_reverse_image_links(self, _discover_profiles):
        upload_stream = io.BytesIO(PNG_BYTES)
        response = self.client.post(
            "/api/search",
            data={
                "username": "shadowseek",
                "image": (upload_stream, "probe.png"),
            },
            content_type="multipart/form-data",
        )

        try:
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            asset_url = payload["reverse_image_links"]["asset_url"]
            self.assertTrue(asset_url.startswith("https://shadowseek.example/api/reverse-image/"))

            asset_path = asset_url.replace("https://shadowseek.example", "")
            asset_response = self.client.get(asset_path)
            try:
                self.assertEqual(asset_response.status_code, 200)
                self.assertEqual(asset_response.mimetype, "image/png")
            finally:
                asset_response.close()
        finally:
            upload_stream.close()
            response.close()

    def test_search_api_validates_username(self):
        response = self.client.post("/api/search", data={"username": "!!"})

        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertIn("username", payload["errors"])

    @patch("app.routes.search.execute_search", side_effect=RuntimeError("boom"))
    def test_search_api_unexpected_error_returns_json(self, _execute_search):
        response = self.client.post("/api/search", data={"username": "shadowseek"})

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(
            response.get_json(),
            {"success": False, "error": "Internal server error"},
        )

    def test_home_page_renders_search_form(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        # Die neue Startseite hat landing-search-form, nicht mehr search-form
        self.assertIn(b'id="landing-search-form"', response.data)
        self.assertIn(b'action="/"', response.data)

    def test_search_page_renders_analysis_containers(self):
        response = self.client.get("/search")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'id="search-form"', response.data)
        self.assertIn(b'id="search-messages"', response.data)
        self.assertIn(b'id="results-list"', response.data)
        self.assertIn(b'id="screenshot-list"', response.data)
        self.assertIn(b'id="similarity-list"', response.data)
        self.assertIn(b'id="image-similarity-list"', response.data)
        self.assertIn(b'id="risk-score-box"', response.data)
        self.assertIn(b"No data available", response.data)

    @patch("app.services.search_service.discover_profiles", return_value=[])
    @patch("app.services.search_service.collect_serper_profiles")
    def test_search_api_prefers_serper_when_available(self, collect_serper_profiles, _discover_profiles):
        collect_serper_profiles.return_value = (
            [
                {
                    "platform": "TikTok",
                    "platform_slug": "tiktok",
                    "category": "social",
                    "username": "shadowseek",
                    "profile_url": "https://www.tiktok.com/@shadowseek",
                    "match_score": 96,
                    "verification": "confirmed",
                    "match_reason": "Direkter Username via Google/Serper",
                    "http_status": 200,
                    "source": "serper",
                    "title": "shadowseek | TikTok",
                    "snippet": "Profil",
                }
            ],
            {"used": True, "queries": 2},
        )
        self.app.config["SERPER_API_KEY"] = "serper-test"

        response = self.client.post("/api/search", data={"username": "shadowseek"})

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["meta"]["serper_used"])
        self.assertEqual(payload["meta"]["serper_queries"], 2)
        self.assertEqual(payload["profiles"][0]["source"], "serper")

    @patch("app.services.search_service.discover_profiles")
    @patch("app.services.search_service.rerank_profiles_with_openai")
    def test_search_api_marks_ai_reranking(self, rerank_profiles_with_openai, discover_profiles):
        discover_profiles.return_value = [
            {
                "platform": "Instagram",
                "platform_slug": "instagram",
                "category": "social",
                "username": "shadowseek",
                "profile_url": "https://www.instagram.com/shadowseek/",
                "match_score": 91,
                "verification": "confirmed",
                "match_reason": "Direkter Username",
                "http_status": 200,
                "source": "direct",
                "title": "",
                "snippet": "",
            },
            {
                "platform": "Reddit",
                "platform_slug": "reddit",
                "category": "community",
                "username": "shadowseek",
                "profile_url": "https://www.reddit.com/user/shadowseek/",
                "match_score": 82,
                "verification": "confirmed",
                "match_reason": "Direkter Username",
                "http_status": 200,
                "source": "direct",
                "title": "",
                "snippet": "",
            },
        ]
        rerank_profiles_with_openai.return_value = (
            [
                {
                    "platform": "Reddit",
                    "platform_slug": "reddit",
                    "category": "community",
                    "username": "shadowseek",
                    "profile_url": "https://www.reddit.com/user/shadowseek/",
                    "match_score": 97,
                    "verification": "ai_reranked",
                    "match_reason": "Handle und Plattformkontext passen am besten.",
                    "http_status": 200,
                    "source": "direct",
                    "title": "",
                    "snippet": "",
                }
            ],
            True,
        )
        self.app.config["OPENAI_API_KEY"] = "openai-test"

        response = self.client.post(
            "/api/search",
            data={"username": "shadowseek", "deep_search": "on"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["meta"]["ai_reranking_applied"])
        self.assertEqual(payload["profiles"][0]["platform"], "Reddit")

    def test_chatbot_endpoint_returns_safe_fallback(self):
        response = self.client.post("/api/chatbot", json={"message": "status"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        # Defensive: Entweder reply oder error-Schlüssel vorhanden
        self.assertTrue("reply" in payload or "error" in payload)

    def test_prod_search_accepts_csrf_token(self):
        with tempfile.TemporaryDirectory() as tempdir:
            prod_config = type(
                "ProdTestConfig",
                (),
                {
                    "TESTING": True,
                    "SECRET_KEY": "prod-secret",
                    "SQLALCHEMY_DATABASE_URI": "sqlite://",
                    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                    "WTF_CSRF_ENABLED": True,
                    "SESSION_COOKIE_SECURE": False,
                    "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
                    "SEARCH_REQUEST_TIMEOUT": 0.1,
                    "SEARCH_MAX_WORKERS": 1,
                    "REVERSE_IMAGE_MAX_AGE": 3600,
                    "PUBLIC_BASE_URL": "https://shadowseek.example",
                    "UPLOAD_DIRECTORY": tempdir,
                    "SERPER_API_KEY": None,
                    "OPENAI_API_KEY": None,
                    "OPENAI_MAX_RERANK_CANDIDATES": 12,
                },
            )
            app = create_app(prod_config)
            client = app.test_client()
            home_response = client.get("/")
            token = extract_csrf_token(home_response.get_data(as_text=True))

            response = client.post(
                "/api/search",
                data={"username": "shadowseek", "csrf_token": token},
                headers={"X-CSRFToken": token},
            )

        self.assertEqual(response.status_code, 200)

    def test_prod_chatbot_accepts_csrf_header(self):
        with tempfile.TemporaryDirectory() as tempdir:
            prod_config = type(
                "ProdChatbotConfig",
                (),
                {
                    "TESTING": True,
                    "SECRET_KEY": "prod-secret",
                    "SQLALCHEMY_DATABASE_URI": "sqlite://",
                    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                    "WTF_CSRF_ENABLED": True,
                    "SESSION_COOKIE_SECURE": False,
                    "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
                    "SEARCH_REQUEST_TIMEOUT": 0.1,
                    "SEARCH_MAX_WORKERS": 1,
                    "REVERSE_IMAGE_MAX_AGE": 3600,
                    "PUBLIC_BASE_URL": "https://shadowseek.example",
                    "UPLOAD_DIRECTORY": tempdir,
                    "SERPER_API_KEY": None,
                    "OPENAI_API_KEY": None,
                    "OPENAI_MAX_RERANK_CANDIDATES": 12,
                },
            )
            app = create_app(prod_config)
            client = app.test_client()
            home_response = client.get("/")
            token = extract_csrf_token(home_response.get_data(as_text=True))

            response = client.post(
                "/api/chatbot",
                json={"message": "status"},
                headers={"X-CSRFToken": token},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue("reply" in payload or "error" in payload)

    def test_create_app_uses_prod_config_on_render(self):
        with patch.dict(
            os.environ,
            {
                "RENDER_EXTERNAL_HOSTNAME": "shadowseek.onrender.com",
                "SECRET_KEY": "prod-secret",
            },
            clear=False,
        ):
            import app.config as config_module

            importlib.reload(config_module)
            prod_app = create_app()

        self.assertFalse(prod_app.config["DEBUG"])
        self.assertTrue(prod_app.config["WTF_CSRF_ENABLED"])
        self.assertEqual(prod_app.config["SECRET_KEY"], "prod-secret")


if __name__ == "__main__":
    unittest.main()
