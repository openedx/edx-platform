import mimetypes

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse


class MarketingSiteViewTests(TestCase):
    """ Tests for the marketing site views """

    def _test_view(self, view_name, mimetype):
        resp = self.client.get(reverse(view_name))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], mimetype)

    def test_sitemap(self):
        """
        Test the sitemap view
        """
        self._test_view('sitemap_xml', 'application/xml')

    def test_about(self):
        """
        Test the about view
        """
        self._test_view('about', 'text/html')
