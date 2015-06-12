# encoding: utf-8
"""Tests of Branding API views. """
import contextlib
import json
import urllib
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

    @ddt.data("*/*", "text/html", "application/json")
    def test_feature_flag(self, accepts):
        self._set_feature_flag(False)
        resp = self._get_footer(accepts=accepts)
        self.assertEqual(resp.status_code, 404)

    @ddt.data(
        # Open source version
        (False, "application/json", "application/json; charset=utf-8", "Open edX"),
        (False, "text/html", "text/html; charset=utf-8", "lms-footer.css"),
        (False, "text/html", "text/html; charset=utf-8", "Open edX"),

        # EdX.org version
        (True, "application/json", "application/json; charset=utf-8", "edX Inc"),
        (True, "text/html", "text/html; charset=utf-8", "lms-footer-edx.css"),
        (True, "text/html", "text/html; charset=utf-8", "edX Inc"),
    )
    @ddt.unpack
    def test_footer_content_types(self, is_edx_domain, accepts, content_type, content):
        self._set_feature_flag(True)
        with self._set_is_edx_domain(is_edx_domain):
            resp = self._get_footer(accepts=accepts)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], content_type)
        self.assertIn(content, resp.content)

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
            self.assertIn("action", link)

        # Mobile links
        self.assertIn("mobile_links", json_data)
        for link in json_data["mobile_links"]:
            self.assertIn("name", link)
            self.assertIn("title", link)
            self.assertIn("url", link)
            self.assertIn("image", link)

        # Legal links
        self.assertIn("legal_links", json_data)
        for link in json_data["legal_links"]:
            self.assertIn("name", link)
            self.assertIn("title", link)
            self.assertIn("url", link)

        # OpenEdX
        self.assertIn("openedx_link", json_data)
        self.assertIn("url", json_data["openedx_link"])
        self.assertIn("title", json_data["openedx_link"])
        self.assertIn("image", json_data["openedx_link"])

        # Copyright
        self.assertIn("copyright", json_data)

    def test_absolute_urls_with_cdn(self):
        self._set_feature_flag(True)

        # Ordinarily, we'd use `override_settings()` to override STATIC_URL,
        # which is what the staticfiles storage backend is using to construct the URL.
        # Unfortunately, other parts of the system are caching this value on module
        # load, which can cause other tests to fail.  To ensure that this change
        # doesn't affect other tests, we patch the `url()` method directly instead.
        cdn_url = "http://cdn.example.com/static/image.png"
        with mock.patch('branding.api.staticfiles_storage.url', return_value=cdn_url):
            resp = self._get_footer()

        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)

        self.assertEqual(json_data["logo_image"], cdn_url)

        for link in json_data["mobile_links"]:
            self.assertEqual(link["url"], cdn_url)

    @ddt.data(
        ("en", "registered trademarks"),
        ("eo", u"régïstéréd trädémärks"),  # Dummy language string
        ("unknown", "registered trademarks"),  # default to English
    )
    @ddt.unpack
    def test_language_override_translation(self, language, expected_copyright):
        self._set_feature_flag(True)

        # Load the footer with the specified language
        resp = self._get_footer(params={'language': language})
        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content)

        # Verify that the translation occurred
        self.assertIn(expected_copyright, json_data['copyright'])

    @ddt.data(
        # OpenEdX
        (False, "en", "lms-footer.css"),
        (False, "ar", "lms-footer-rtl.css"),

        # EdX.org
        (True, "en", "lms-footer-edx.css"),
        (True, "ar", "lms-footer-edx-rtl.css"),
    )
    @ddt.unpack
    def test_language_rtl(self, is_edx_domain, language, static_path):
        self._set_feature_flag(True)

        with self._set_is_edx_domain(is_edx_domain):
            resp = self._get_footer(accepts="text/html", params={'language': language})

        self.assertEqual(resp.status_code, 200)
        self.assertIn(static_path, resp.content)

    @ddt.data(
        # OpenEdX
        (False, True),
        (False, False),

        # EdX.org
        (True, True),
        (True, False),
    )
    @ddt.unpack
    def test_show_openedx_logo(self, is_edx_domain, show_logo):
        self._set_feature_flag(True)

        with self._set_is_edx_domain(is_edx_domain):
            params = {'show-openedx-logo': 1} if show_logo else {}
            resp = self._get_footer(accepts="text/html", params=params)

        self.assertEqual(resp.status_code, 200)

        if show_logo:
            self.assertIn(settings.FOOTER_OPENEDX_URL, resp.content)
        else:
            self.assertNotIn(settings.FOOTER_OPENEDX_URL, resp.content)

    @ddt.data(
        # OpenEdX
        (False, False),
        (False, True),

        # EdX.org
        (True, False),
        (True, True),
    )
    @ddt.unpack
    def test_include_dependencies(self, is_edx_domain, include_dependencies):
        self._set_feature_flag(True)
        with self._set_is_edx_domain(is_edx_domain):
            params = {'include-dependencies': 1} if include_dependencies else {}
            resp = self._get_footer(accepts="text/html", params=params)

        self.assertEqual(resp.status_code, 200)

        if include_dependencies:
            self.assertIn("vendor", resp.content)
        else:
            self.assertNotIn("vendor", resp.content)

    def test_no_supported_accept_type(self):
        self._set_feature_flag(True)
        resp = self._get_footer(accepts="application/x-shockwave-flash")
        self.assertEqual(resp.status_code, 406)

    def _set_feature_flag(self, enabled):
        """Enable or disable the feature flag for the branding API end-points. """
        config = BrandingApiConfig(enabled=enabled)
        config.save()

    def _get_footer(self, accepts="application/json", params=None):
        """Retrieve the footer. """
        url = reverse("branding_footer")

        if params is not None:
            url = u"{url}?{params}".format(
                url=url,
                params=urllib.urlencode(params)
            )

        return self.client.get(url, HTTP_ACCEPT=accepts)

    @contextlib.contextmanager
    def _set_is_edx_domain(self, is_edx_domain):
        """Configure whether this an EdX-controlled domain. """
        with mock.patch.dict(settings.FEATURES, {'IS_EDX_DOMAIN': is_edx_domain}):
            yield
