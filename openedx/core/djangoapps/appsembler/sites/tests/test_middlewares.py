"""
Tests for the sites.middlewares module.
"""

from mock import patch, Mock
from django.test import TestCase, override_settings
from django.test.client import RequestFactory

from openedx.core.djangoapps.appsembler.sites.middleware import LmsCurrentOrganizationMiddleware, RedirectMiddleware
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory


@patch('openedx.core.djangoapps.appsembler.sites.middleware.get_current_organization')
class LmsCurrentOrganizationMiddlewareTests(TestCase):
    def test_with_organization(self, get_current_organization):
        middleware = LmsCurrentOrganizationMiddleware()
        request = Mock(session={})
        fake_org = Mock()
        get_current_organization.return_value = fake_org

        middleware.process_request(request)
        assert request.session['organization'] is fake_org

    def test_with_no_organization(self, get_current_organization):
        middleware = LmsCurrentOrganizationMiddleware()
        request = Mock(session={})
        get_current_organization.return_value = None

        middleware.process_request(request)
        assert request.session['organization'] is None


@override_settings(TAHOE_MAIN_SITE_REDIRECT_URL='https://foo.bar')
@override_settings(MAIN_SITE_REDIRECT_ALLOWLIST=['/baz'])
class RedirectMiddlewareTests(TestCase):
    def setUp(self):
        super(RedirectMiddlewareTests, self).setUp()
        self.default_site = SiteFactory.create()
        self.other_site = SiteFactory.create()
        patcher = patch("django.conf.settings.SITE_ID", self.default_site.id)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_redirects_default_site(self):
        request = RequestFactory().get('/path', HTTP_HOST=self.default_site.domain)
        request.site = self.default_site
        processed = RedirectMiddleware().process_request(request)
        self.assertEquals(processed.url, 'https://foo.bar')  # middleware drops the path

    def test_with_no_site_found(self):
        request = RequestFactory().get('/')
        request.site = None
        processed = RedirectMiddleware().process_request(request)
        self.assertIsNone(processed)

    def test_no_redirect_other_site(self):
        request = RequestFactory().get('/', HTTP_HOST=self.other_site.domain)
        request.site = self.other_site
        processed = RedirectMiddleware().process_request(request)
        self.assertIsNone(processed)

    def test_url_in_whitelist(self):
        request = RequestFactory().get('/baz', HTTP_HOST=self.default_site.domain)
        request.site = self.default_site
        processed = RedirectMiddleware().process_request(request)
        self.assertIsNone(processed)
