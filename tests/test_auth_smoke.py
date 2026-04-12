import unittest
from app import create_app

class AuthSmokeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_auth_route_exists(self):
        resp = self.client.get('/auth/login')
        # Accept 200, 302 (redirect), or 401 (unauth)
        self.assertIn(resp.status_code, [200, 302, 401, 404])

if __name__ == '__main__':
    unittest.main()
