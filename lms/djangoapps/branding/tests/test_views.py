# encoding: utf-8
"""
Tests of branding api views.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
import json
from branding.models import BrandingApiConfig


class TestFooter(TestCase):
    """ Test for getting the footer data as json
    """

    def test_footer(self):
        """ Test the footer json
        """
        config = BrandingApiConfig(enabled=True)
        config.save()
        url = reverse("get_footer_data")
        footer_data = self.client.get(url, HTTP_ACCEPT="application/json")
        json_data = json.loads(footer_data.content)

        self.assertIn("footer", json_data)
        self.assertIn("about_links", json_data["footer"])
        self.assertIn("social_links", json_data["footer"])
        self.assertIn("heading", json_data["footer"])
