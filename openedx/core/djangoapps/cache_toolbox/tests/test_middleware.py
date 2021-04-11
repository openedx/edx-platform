"""Tests for cached authentication middleware."""


from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import TestCase
from mock import patch

from openedx.core.djangolib.testing.utils import skip_unless_cms, skip_unless_lms
from common.djangoapps.student.tests.factories import UserFactory


class CachedAuthMiddlewareTestCase(TestCase):
    """Tests for CacheBackedAuthenticationMiddleware class."""

    def setUp(self):
        super(CachedAuthMiddlewareTestCase, self).setUp()
        password = 'test-password'
        self.user = UserFactory(password=password)
        self.client.login(username=self.user.username, password=password)

    def _test_change_session_hash(self, test_url, redirect_url, target_status_code=200):
        """
        Verify that if a user's session auth hash and the request's hash
        differ, the user is logged out. The URL to test and the
        expected redirect are passed in, since we want to test this
        behavior in both LMS and CMS, but the two systems have
        different URLconfs.
        """
        response = self.client.get(test_url)
        self.assertEqual(response.status_code, 200)
        with patch.object(User, 'get_session_auth_hash', return_value='abc123'):
            response = self.client.get(test_url)
            self.assertRedirects(response, redirect_url, target_status_code=target_status_code)

    @skip_unless_lms
    def test_session_change_lms(self):
        """Test session verification with LMS-specific URLs."""
        dashboard_url = reverse('dashboard')
        self._test_change_session_hash(dashboard_url, reverse('signin_user') + '?next=' + dashboard_url)

    @skip_unless_cms
    def test_session_change_cms(self):
        """Test session verification with CMS-specific URLs."""
        home_url = reverse('home')
        # Studio login redirects to LMS login
        self._test_change_session_hash(home_url, settings.LOGIN_URL + '?next=' + home_url, target_status_code=302)
