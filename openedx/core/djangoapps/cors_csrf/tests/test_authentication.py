"""Tests for the CORS CSRF version of Django Rest Framework's SessionAuthentication."""
from mock import patch

from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory
from django.conf import settings

from rest_framework.exceptions import PermissionDenied

from ..authentication import SessionAuthenticationCrossDomainCsrf


class CrossDomainAuthTest(TestCase):
    """Tests for the CORS CSRF version of Django Rest Framework's SessionAuthentication. """

    URL = "/dummy_url"
    REFERER = "https://www.edx.org"
    CSRF_TOKEN = 'abcd1234'

    def setUp(self):
        super(CrossDomainAuthTest, self).setUp()
        self.auth = SessionAuthenticationCrossDomainCsrf()

    def test_perform_csrf_referer_check(self):
        request = self._fake_request()
        with self.assertRaisesRegexp(PermissionDenied, 'CSRF'):
            self.auth.enforce_csrf(request)

    @patch.dict(settings.FEATURES, {
        'ENABLE_CORS_HEADERS': True,
        'ENABLE_CROSS_DOMAIN_CSRF_COOKIE': True
    })
    @override_settings(
        CORS_ORIGIN_WHITELIST=["www.edx.org"],
        CROSS_DOMAIN_CSRF_COOKIE_NAME="prod-edx-csrftoken",
        CROSS_DOMAIN_CSRF_COOKIE_DOMAIN=".edx.org"
    )
    def test_skip_csrf_referer_check(self):
        request = self._fake_request()
        result = self.auth.enforce_csrf(request)
        self.assertIs(result, None)
        self.assertTrue(request.is_secure())

    def _fake_request(self):
        """Construct a fake request with a referer and CSRF token over a secure connection. """
        factory = RequestFactory()
        factory.cookies[settings.CSRF_COOKIE_NAME] = self.CSRF_TOKEN

        request = factory.post(
            self.URL,
            HTTP_REFERER=self.REFERER,
            HTTP_X_CSRFTOKEN=self.CSRF_TOKEN
        )
        request.is_secure = lambda: True
        return request
