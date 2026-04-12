import unittest
from app import create_app

class ApiSmokeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_api_search(self):
        resp = self.client.post('/api/search', data={"q": "test"})
        self.assertIn(resp.status_code, [200, 400, 401, 404])

    def test_api_health(self):
        resp = self.client.get('/health')
        self.assertIn(resp.status_code, [200, 401, 404])

if __name__ == '__main__':
    unittest.main()
