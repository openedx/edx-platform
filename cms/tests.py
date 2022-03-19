""" Api Doc test """
from django.conf import settings
from django.test import TestCase


class TestAPIDoc(TestCase):
    """
    Api Doc test
    """
    def test_api_docs(self):
        """
        Tests that requests to the `/api-docs/` endpoint do not raise an exception.
        """
        response = self.client.get('/api-docs/')
        self.assertFalse(settings.FEATURES.get('TAHOE_ENABLE_API_DOCS_URLS'))
        self.assertEqual(404, response.status_code)  # Tahoe: Changed from `200`
