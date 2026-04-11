import io
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


if __name__ == "__main__":
    unittest.main()
