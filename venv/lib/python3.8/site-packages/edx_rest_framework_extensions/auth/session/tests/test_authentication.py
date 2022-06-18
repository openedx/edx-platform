""" Test for SessionAuthenticationAllowInactiveUser class """
from django.test import RequestFactory, TestCase

from edx_rest_framework_extensions.auth.session.authentication import (
    SessionAuthenticationAllowInactiveUser,
)
from edx_rest_framework_extensions.tests import factories


class SessionAuthenticationAllowInactiveUserTests(TestCase):
    def setUp(self):
        super().setUp()
        self.user = factories.UserFactory(
            email='inactive', username='inactive@example.com', password='dummypassword', is_active=False
        )
        self.request = RequestFactory().get('/')

    def test_authenticate(self):
        """Verify inactive user is authenticated."""
        self.request.user = self.user
        self.request._request = self.request  # pylint: disable=protected-access
        user, _ = SessionAuthenticationAllowInactiveUser().authenticate(self.request)
        self.assertEqual(user, self.user)

    def test_user_not_exist(self):
        """Verify request with no user return None."""
        self.request._request = self.request  # pylint: disable=protected-access
        user = SessionAuthenticationAllowInactiveUser().authenticate(self.request)
        self.assertEqual(user, None)
