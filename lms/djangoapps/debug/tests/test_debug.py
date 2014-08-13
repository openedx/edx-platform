from django.test import TestCase
from django.test.client import Client


class TestDebugUrls(TestCase):
    def setUp(self):
        self.client = Client()

    def test_404_error(self):
        response = self.client.get("/404")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(response.content)

    def test_500_error(self):
        response = self.client.get("/500")
        self.assertEqual(response.status_code, 500)
        self.assertTrue(response.content)
