""" Test User Authentication utilities """

import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings

from openedx.core.djangoapps.user_authn.utils import is_safe_login_or_logout_redirect


@ddt.ddt
class TestRedirectUtils(TestCase):
    """Test redirect utility methods."""

    def setUp(self):
        super(TestRedirectUtils, self).setUp()
        self.request = RequestFactory()

    @ddt.data(
        ('/dashboard', 'testserver', True),
        ('https://edx.org/courses', 'edx.org', True),
        ('https://test.edx.org/courses', 'edx.org', True),
        ('https://www.amazon.org', 'edx.org', False),
        ('http://edx.org/courses', 'edx.org', False),
        ('http:///edx.org/courses', 'edx.org', False),  # Django's is_safe_url protects against "///"
    )
    @ddt.unpack
    @override_settings(LOGIN_REDIRECT_WHITELIST=['test.edx.org'])
    def test_safe_redirect(self, url, host, expected_is_safe):
        """ Test safe next parameter """
        req = self.request.get('/login', HTTP_HOST=host)
        actual_is_safe = is_safe_login_or_logout_redirect(req, url)
        self.assertEqual(actual_is_safe, expected_is_safe)
