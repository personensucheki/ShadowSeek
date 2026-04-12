import unittest
from app import create_app

class FactorySmokeTest(unittest.TestCase):
    def test_app_factory(self):
        app = create_app()
        self.assertIsNotNone(app)
        self.assertTrue(hasattr(app, 'config'))
        self.assertTrue(callable(app.test_client))

    def test_blueprints_registered(self):
        app = create_app()
        with app.app_context():
            # At least one blueprint should be registered
            self.assertGreater(len(app.blueprints), 0)
            # Check for a known blueprint
            self.assertIn('search', app.blueprints)

if __name__ == '__main__':
    unittest.main()
