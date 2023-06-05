# encoding: utf-8
"""Tests of Branding API views. """


import json

import ddt
import mock
import six
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from lms.djangoapps.branding.models import BrandingApiConfig
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.lang_pref.api import released_languages
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme_context
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase
from common.djangoapps.student.tests.factories import UserFactory


@ddt.ddt
class TestFooter(CacheIsolationTestCase):
    """Test API end-point for retrieving the footer. """

    @ddt.data("*/*", "text/html", "application/json")
    def test_feature_flag(self, accepts):
        self._set_feature_flag(False)
        resp = self._get_footer(accepts=accepts)
        self.assertEqual(resp.status_code, 404)

    @ddt.data(
        # Open source version
        (None, "application/json", "application/json; charset=utf-8", "Open edX"),
        (None, "text/html", "text/html; charset=utf-8", "lms-footer.css"),
        (None, "text/html", "text/html; charset=utf-8", "Open edX"),

        # EdX.org version
        ("edx.org", "application/json", "application/json; charset=utf-8", "edX Inc"),
        ("edx.org", "text/html", "text/html; charset=utf-8", "lms-footer-edx.css"),
        ("edx.org", "text/html", "text/html; charset=utf-8", "edX Inc"),
    )
    @ddt.unpack
    def test_footer_content_types(self, theme, accepts, content_type, content):
        self._set_feature_flag(True)
        with with_comprehensive_theme_context(theme):
            resp = self._get_footer(accepts=accepts)

        self.assertEqual(resp["Content-Type"], content_type)
        self.assertContains(resp, content)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_FOOTER_MOBILE_APP_LINKS': True})
    @ddt.data("edx.org", None)
    def test_footer_json(self, theme):
        self._set_feature_flag(True)
        with with_comprehensive_theme_context(theme):
            resp = self._get_footer()

        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content.decode('utf-8'))
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
        with mock.patch('lms.djangoapps.branding.api.staticfiles_storage.url', return_value=cdn_url):
            resp = self._get_footer()

        self.assertEqual(resp.status_code, 200)
        json_data = json.loads(resp.content.decode('utf-8'))

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
        json_data = json.loads(resp.content.decode('utf-8'))

        # Verify that the translation occurred
        self.assertIn(expected_copyright, json_data['copyright'])

    @ddt.data(
        # OpenEdX
        (None, "en", "lms-footer.css"),
        (None, "ar", "lms-footer-rtl.css"),

        # EdX.org
        ("edx.org", "en", "lms-footer-edx.css"),
        ("edx.org", "ar", "lms-footer-edx-rtl.css"),
    )
    @ddt.unpack
    def test_language_rtl(self, theme, language, static_path):
        self._set_feature_flag(True)

        with with_comprehensive_theme_context(theme):
            resp = self._get_footer(accepts="text/html", params={'language': language})

        self.assertContains(resp, static_path)

    @ddt.data(
        # OpenEdX
        (None, True),
        (None, False),

        # EdX.org
        ("edx.org", True),
        ("edx.org", False),
    )
    @ddt.unpack
    def test_show_openedx_logo(self, theme, show_logo):
        self._set_feature_flag(True)

        with with_comprehensive_theme_context(theme):
            params = {'show-openedx-logo': 1} if show_logo else {}
            resp = self._get_footer(accepts="text/html", params=params)

        if show_logo:
            self.assertContains(resp, 'alt="Powered by Open edX"')
        else:
            self.assertNotContains(resp, 'alt="Powered by Open edX"')

    @ddt.data(
        # OpenEdX
        (None, False),
        (None, True),

        # EdX.org
        ("edx.org", False),
        ("edx.org", True),
    )
    @ddt.unpack
    def test_include_dependencies(self, theme, include_dependencies):
        self._set_feature_flag(True)
        with with_comprehensive_theme_context(theme):
            params = {'include-dependencies': 1} if include_dependencies else {}
            resp = self._get_footer(accepts="text/html", params=params)

        if include_dependencies:
            self.assertContains(resp, "vendor",)
        else:
            self.assertNotContains(resp, "vendor")

    @ddt.data(
        # OpenEdX
        (None, None, '1'),
        (None, 'eo', '1'),
        (None, None, ''),

        # EdX.org
        ('edx.org', None, '1'),
        ('edx.org', 'eo', '1'),
        ('edx.org', None, '')
    )
    @ddt.unpack
    def test_include_language_selector(self, theme, language, include_language_selector):
        self._set_feature_flag(True)
        DarkLangConfig(released_languages='en,eo,es-419,fr', enabled=True, changed_by=User().save()).save()

        with with_comprehensive_theme_context(theme):
            params = {
                key: val for key, val in [
                    ('language', language), ('include-language-selector', include_language_selector)
                ] if val
            }
            resp = self._get_footer(accepts="text/html", params=params)

        self.assertEqual(resp.status_code, 200)

        if include_language_selector:
            selected_language = language if language else 'en'
            self._verify_language_selector(resp, selected_language)
        else:
            self.assertNotContains(resp, 'footer-language-selector')

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
                params=six.moves.urllib.parse.urlencode(params)
            )

        return self.client.get(url, HTTP_ACCEPT=accepts)

    def _verify_language_selector(self, response, selected_language):
        """ Verify that the language selector is present and correctly configured."""
        # Verify the selector is included
        content = response.content.decode(response.charset)
        self.assertIn('footer-language-selector', content)

        # Verify the correct language is selected
        self.assertIn(u'<option value="{}" selected="selected">'.format(selected_language), content)

        # Verify the language choices
        for language in released_languages():
            if language.code == selected_language:
                continue
            self.assertIn(u'<option value="{}">'.format(language.code), content)


class TestIndex(SiteMixin, TestCase):
    """ Test the index view """

    def setUp(self):
        """ Set up a user """
        super(TestIndex, self).setUp()

        patcher = mock.patch("common.djangoapps.student.models.tracker")
        self.mock_tracker = patcher.start()
        self.user = UserFactory.create()
        self.user.set_password("password")
        self.user.save()

    def test_index_does_not_redirect_without_site_override(self):
        """ Test index view does not redirect if MKTG_URLS['ROOT'] is not set """
        response = self.client.get(reverse("root"))
        self.assertEqual(response.status_code, 200)

    def test_index_redirects_to_marketing_site_with_site_override(self):
        """ Test index view redirects if MKTG_URLS['ROOT'] is set in SiteConfiguration """
        self.use_site(self.site_other)
        response = self.client.get(reverse("root"))
        self.assertRedirects(
            response,
            self.site_configuration_other.site_values["MKTG_URLS"]["ROOT"],
            fetch_redirect_response=False
        )

    def test_header_logo_links_to_marketing_site_with_site_override(self):
        """
        Test marketing site root link is included on dashboard page
        if MKTG_URLS['ROOT'] is set in SiteConfiguration
        """
        self.use_site(self.site_other)
        self.client.login(username=self.user.username, password="password")
        response = self.client.get(reverse("dashboard"))
        self.assertIn(self.site_configuration_other.site_values["MKTG_URLS"]["ROOT"], response.content.decode('utf-8'))
