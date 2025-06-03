"""Tests of Branding API views. """


import json
from unittest import mock

import ddt
import six
from django.conf import settings
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.test import TestCase
from django.urls import reverse
from edx_toggles.toggles.testutils import override_waffle_flag

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.branding.models import BrandingApiConfig
from lms.djangoapps.branding.toggles import (
    ENABLE_NEW_CATALOG_PAGE,
    ENABLE_NEW_COURSE_ABOUT_PAGE,
)
from openedx.core.djangoapps.dark_lang.models import DarkLangConfig
from openedx.core.djangoapps.lang_pref.api import released_languages
from openedx.core.djangoapps.site_configuration.tests.mixins import SiteMixin
from openedx.core.djangoapps.theming.tests.test_util import with_comprehensive_theme_context
from openedx.core.djangolib.testing.utils import CacheIsolationTestCase


@ddt.ddt
class TestFooter(CacheIsolationTestCase):
    """Test API end-point for retrieving the footer. """

    @ddt.data("*/*", "text/html", "application/json")
    def test_feature_flag(self, accepts):
        self._set_feature_flag(False)
        resp = self._get_footer(accepts=accepts)
        assert resp.status_code == 404

    @ddt.data(
        # Open source version
        (None, "application/json", "application/json; charset=utf-8", "Open edX"),
        (None, "text/html", "text/html; charset=utf-8", "lms-footer.css"),
        (None, "text/html", "text/html; charset=utf-8", "Open edX"),
    )
    @ddt.unpack
    def test_footer_content_types(self, theme, accepts, content_type, content):
        self._set_feature_flag(True)
        with with_comprehensive_theme_context(theme):
            resp = self._get_footer(accepts=accepts)

        assert resp['Content-Type'] == content_type
        self.assertContains(resp, content)

    @mock.patch.dict(settings.FEATURES, {'ENABLE_FOOTER_MOBILE_APP_LINKS': True})
    def test_footer_json(self):
        self._set_feature_flag(True)
        with with_comprehensive_theme_context(None):
            resp = self._get_footer()

        assert resp.status_code == 200
        json_data = json.loads(resp.content.decode('utf-8'))
        assert isinstance(json_data, dict)

        # Logo
        assert 'logo_image' in json_data

        # Links
        assert 'navigation_links' in json_data
        for link in json_data["navigation_links"]:
            assert 'name' in link
            assert 'title' in link
            assert 'url' in link

        # Social links
        assert 'social_links' in json_data
        for link in json_data["social_links"]:
            assert 'name' in link
            assert 'title' in link
            assert 'url' in link
            assert 'icon-class' in link
            assert 'action' in link

        # Mobile links
        assert 'mobile_links' in json_data
        for link in json_data["mobile_links"]:
            assert 'name' in link
            assert 'title' in link
            assert 'url' in link
            assert 'image' in link

        # Legal links
        assert 'legal_links' in json_data
        for link in json_data["legal_links"]:
            assert 'name' in link
            assert 'title' in link
            assert 'url' in link

        # OpenEdX
        assert 'openedx_link' in json_data
        assert 'url' in json_data['openedx_link']
        assert 'title' in json_data['openedx_link']
        assert 'image' in json_data['openedx_link']

        # Copyright
        assert 'copyright' in json_data

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

        assert resp.status_code == 200
        json_data = json.loads(resp.content.decode('utf-8'))

        assert json_data['logo_image'] == cdn_url

        for link in json_data["mobile_links"]:
            assert link['url'] == cdn_url

    @ddt.data(
        ("en", "registered trademarks"),
        ("eo", "régïstéréd trädémärks"),  # Dummy language string
        ("unknown", "registered trademarks"),  # default to English
    )
    @ddt.unpack
    def test_language_override_translation(self, language, expected_copyright):
        self._set_feature_flag(True)

        # Load the footer with the specified language
        resp = self._get_footer(params={'language': language})
        assert resp.status_code == 200
        json_data = json.loads(resp.content.decode('utf-8'))

        # Verify that the translation occurred
        assert expected_copyright in json_data['copyright']

    @ddt.data(
        # OpenEdX
        (None, "en", "lms-footer.css"),
        (None, "ar", "lms-footer-rtl.css"),
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

        assert resp.status_code == 200

        if include_language_selector:
            selected_language = language if language else 'en'
            self._verify_language_selector(resp, selected_language)
        else:
            self.assertNotContains(resp, 'footer-language-selector')

    def test_no_supported_accept_type(self):
        self._set_feature_flag(True)
        resp = self._get_footer(accepts="application/x-shockwave-flash")
        assert resp.status_code == 406

    def _set_feature_flag(self, enabled):
        """Enable or disable the feature flag for the branding API end-points. """
        config = BrandingApiConfig(enabled=enabled)
        config.save()

    def _get_footer(self, accepts="application/json", params=None):
        """Retrieve the footer. """
        url = reverse("branding_footer")

        if params is not None:
            url = "{url}?{params}".format(
                url=url,
                params=six.moves.urllib.parse.urlencode(params)
            )

        return self.client.get(url, HTTP_ACCEPT=accepts)

    def _verify_language_selector(self, response, selected_language):
        """ Verify that the language selector is present and correctly configured."""
        # Verify the selector is included
        content = response.content.decode(response.charset)
        assert 'footer-language-selector' in content

        # Verify the correct language is selected
        assert f'<option value="{selected_language}" selected="selected">' in content

        # Verify the language choices
        for language in released_languages():
            if language.code == selected_language:
                continue
            assert f'<option value="{language.code}">' in content


class TestIndex(SiteMixin, TestCase):
    """ Test the index view """

    def setUp(self):
        """ Set up a user """
        super().setUp()

        patcher = mock.patch("common.djangoapps.student.models.course_enrollment.tracker")
        self.mock_tracker = patcher.start()
        self.user = UserFactory.create()
        self.user.set_password("password")
        self.user.save()

    def test_index_does_not_redirect_without_site_override(self):
        """ Test index view does not redirect if MKTG_URLS['ROOT'] is not set """
        response = self.client.get(reverse("root"))
        assert response.status_code == 200

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
        assert self.site_configuration_other.site_values['MKTG_URLS']['ROOT'] in response.content.decode('utf-8')


@ddt.ddt
class TestWaffleFlags(TestCase):
    """Tests for the waffle_flags view."""

    def setUp(self):
        super().setUp()
        self.url = reverse("branding_waffle_flags")
        self.user = UserFactory.create()
        self.user.set_password("password")
        self.user.save()

    @ddt.data(True, False)
    @override_waffle_flag(ENABLE_NEW_CATALOG_PAGE, False)
    @override_waffle_flag(ENABLE_NEW_COURSE_ABOUT_PAGE, True)
    def test_anonymous_access(self, new_index_page_value):
        """Test that anonymous users can access the waffle flags endpoint."""
        with mock.patch('lms.djangoapps.branding.toggles.use_new_index_page', return_value=new_index_page_value):
            response = self.client.get(self.url)

            assert response.status_code == 200
            assert response['Content-Type'] == 'application/json'

            data = json.loads(response.content.decode('utf-8'))
            assert data['use_new_index_page'] == new_index_page_value
            assert data['use_new_catalog_page'] is False
            assert data['use_new_course_about_page'] is True

    @ddt.data(True, False)
    @override_waffle_flag(ENABLE_NEW_CATALOG_PAGE, True)
    @override_waffle_flag(ENABLE_NEW_COURSE_ABOUT_PAGE, False)
    def test_authenticated_access(self, new_index_page_value):
        """Test that authenticated users can access the waffle flags endpoint."""
        self.client.login(username=self.user.username, password="password")

        with mock.patch('lms.djangoapps.branding.toggles.use_new_index_page', return_value=new_index_page_value):
            response = self.client.get(self.url)

            assert response.status_code == 200
            assert response['Content-Type'] == 'application/json'

            data = json.loads(response.content.decode('utf-8'))
            assert data['use_new_index_page'] == new_index_page_value
            assert data['use_new_catalog_page'] is True
            assert data['use_new_course_about_page'] is False

    @ddt.data(
        (True, True, True),
        (True, False, True),
        (False, True, False),
        (False, False, False)
    )
    @ddt.unpack
    def test_various_flag_combinations(self, new_index, new_catalog, new_course_about):
        """Test the endpoint with different combinations of flag values."""
        with mock.patch('lms.djangoapps.branding.toggles.use_new_index_page', return_value=new_index):
            with mock.patch('lms.djangoapps.branding.toggles.use_new_catalog_page', return_value=new_catalog):
                with mock.patch(
                    'lms.djangoapps.branding.toggles.use_new_course_about_page', return_value=new_course_about
                ):
                    response = self.client.get(self.url)

                    assert response.status_code == 200
                    data = json.loads(response.content.decode('utf-8'))

                    assert data['use_new_index_page'] == new_index
                    assert data['use_new_catalog_page'] == new_catalog
                    assert data['use_new_course_about_page'] == new_course_about

    def test_response_structure(self):
        """Test that the response contains the expected structure."""
        response = self.client.get(self.url)

        assert response.status_code == 200
        data = json.loads(response.content.decode('utf-8'))

        assert 'use_new_index_page' in data
        assert 'use_new_catalog_page' in data
        assert 'use_new_course_about_page' in data
