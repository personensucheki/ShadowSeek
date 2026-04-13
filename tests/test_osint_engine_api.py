import io
import tempfile
import unittest

from PIL import Image

from app import create_app
from app.extensions.main import db


def build_png_bytes():
    buffer = io.BytesIO()
    image = Image.new("RGB", (8, 8), (255, 0, 255))
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class OsintEngineApiTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()
        cfg = type(
            "OsintTestConfig",
            (),
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "SQLALCHEMY_TRACK_MODIFICATIONS": False,
                "WTF_CSRF_ENABLED": False,
                "SESSION_COOKIE_SECURE": False,
                "MAX_CONTENT_LENGTH": 3 * 1024 * 1024,
                "UPLOAD_DIRECTORY": self.temp_directory.name,
                "OSINT_ENGINE_ENABLED": True,
                "OPENAI_API_KEY": None,
                "YOUTUBE_API_KEY": None,
            },
        )
        self.app = create_app(cfg)
        with self.app.app_context():
            db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.temp_directory.cleanup()

    def _assert_envelope(self, payload):
        self.assertIn("success", payload)
        self.assertIn("data", payload)
        self.assertIn("error", payload)
        self.assertIn("meta", payload)

    def test_identity_match_envelope(self):
        response = self.client.post("/api/identity/match", json={"username": "shadowseek"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self._assert_envelope(payload)
        self.assertTrue(payload["success"])
        self.assertIn("profiles", payload["data"])

    def test_username_check_envelope(self):
        response = self.client.post("/api/username/check", json={"username": "shadowseek", "platforms": ["tiktok"]})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self._assert_envelope(payload)
        self.assertTrue(payload["success"])
        self.assertIn("results", payload["data"])

    def test_reverse_image_missing_file_envelope(self):
        response = self.client.post("/api/reverse-image", data={}, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self._assert_envelope(payload)
        self.assertFalse(payload["success"])

    def test_reverse_image_success_envelope(self):
        stream = io.BytesIO(build_png_bytes())
        response = self.client.post(
            "/api/reverse-image",
            data={"image": (stream, "probe.png"), "source_platform": "tiktok", "source_profile": "shadowseek"},
            content_type="multipart/form-data",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self._assert_envelope(payload)
        self.assertIn("possible_matches", payload["data"])
        self.assertIn("hashes", payload["data"])


if __name__ == "__main__":
    unittest.main()
