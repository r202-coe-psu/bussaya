import unittest

from bussaya import create_app


class FirstPageTest(unittest.TestCase):
    def setUp(self):
        # creates a test client
        app = create_app()
        self.client = app.test_client()
        self.client.testing = True

    def test_first_page(self):
        result = self.client.get('/')
        self.assertEqual(result.status_code, 200)
        self.assertIn('Bussaya', result.data.decode())
