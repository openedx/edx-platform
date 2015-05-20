# encoding: utf-8
"""Tests of Branding API views. """

import contextlib
import json
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings

import mock
import ddt
from config_models.models import cache
from branding.models import BrandingApiConfig


@ddt.ddt
class TestFooter(TestCase):
    """Test API end-point for retrieving the footer. """

    def setUp(self):
        """Clear the configuration cache. """
        super(TestFooter, self).setUp()
        cache.clear()

    @ddt.data("", "css", "js", "html")
    def test_feature_flag(self, extension):
        self._set_feature_flag(False)
        resp = self._get_footer(extension=extension)
        self.assertEqual(resp.status_code, 404)

    @ddt.data(
        # Open source version
        (False, "", "application/json; charset=utf-8"),
        (False, "css", "text/css"),
        (False, "js", "text/javascript"),
        (False, "html", "text/html; charset=utf-8"),

        # EdX.org version
        (True, "", "application/json; charset=utf-8"),
        (True, "css", "text/css"),
        (True, "js", "text/javascript"),
        (True, "html", "text/html; charset=utf-8"),
    )
    @ddt.unpack
    def test_footer_content_types(self, is_edx_domain, extension, content_type):
        self._set_feature_flag(True)
        with self._set_is_edx_domain(is_edx_domain):
            resp = self._get_footer(extension=extension)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], content_type)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_FOOTER_MOBILE_APP_LINKS': True})
    @ddt.data(True, False)
    def test_footer_json(self, is_edx_domain):
        self._set_feature_flag(True)
        with self._set_is_edx_domain(is_edx_domain):
            resp = self._get_footer()

        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)
        self.assertTrue(isinstance(json_data, dict))

        # Logo
        self.assertIn("logo_image", json_data)

        # Links
        self.assertIn("navigation_links", json_data)
        for link in json_data["navigation_links"]:
            self.assertIn("name", link)
            self.assertIn("title", link)
            self.assertIn("url", link)

        # Social links
        self.assertIn("social_links", json_data)
        for link in json_data["social_links"]:
            self.assertIn("name", link)
            self.assertIn("title", link)
            self.assertIn("url", link)
            self.assertIn("icon-class", link)

        # Mobile links
        self.assertIn("mobile_links", json_data)
        for link in json_data["mobile_links"]:
            self.assertIn("name", link)
            self.assertIn("title", link)
            self.assertIn("url", link)
            self.assertIn("image", link)

        # OpenEdX
        self.assertIn("openedx_link", json_data)
        self.assertIn("url", json_data["openedx_link"])
        self.assertIn("title", json_data["openedx_link"])
        self.assertIn("image", json_data["openedx_link"])

        # Copyright
        self.assertIn("copyright", json_data)

    def _set_feature_flag(self, enabled):
        """Enable or disable the feature flag for the branding API end-points. """
        config = BrandingApiConfig(enabled=enabled)
        config.save()

    def _get_footer(self, extension=""):
        """Retrieve the footer. """
        url = reverse("branding_footer")
        if extension:
            url = u"{url}.{ext}".format(url=url, ext=extension)
        return self.client.get(url)

    @contextlib.contextmanager
    def _set_is_edx_domain(self, is_edx_domain):
        """Configure whether this an EdX-controlled domain. """
        with mock.patch.dict(settings.FEATURES, {'IS_EDX_DOMAIN': is_edx_domain}):
            yield
