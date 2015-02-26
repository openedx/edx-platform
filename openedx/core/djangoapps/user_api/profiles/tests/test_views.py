"""
Unit tests for profile APIs.
"""

import ddt
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse

from openedx.core.djangoapps.user_api.accounts.tests.test_views import UserAPITestCase
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.profiles import PROFILE_VISIBILITY_PREF_KEY
from .. import PRIVATE_VISIBILITY


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Profile APIs are only supported in LMS')
class TestProfileAPI(UserAPITestCase):
    """
    Unit tests for the profile API.
    """

    def setUp(self):
        super(TestProfileAPI, self).setUp()
        self.url = reverse("profiles_api", kwargs={'username': self.user.username})

    def test_get_profile_anonymous_user(self):
        """
        Test that an anonymous client (not logged in) cannot call get.
        """
        self.send_get(self.anonymous_client, expected_status=401)

    def _verify_full_profile_response(self, response):
        """
        Verify that all of the profile's fields are returned
        """
        data = response.data
        self.assertEqual(6, len(data))
        self.assertEqual(self.user.username, data["username"])
        self.assertEqual("US", data["country"])
        self.assertIsNone(data["profile_image"])
        self.assertIsNone(data["time_zone"])
        self.assertIsNone(data["languages"])
        self.assertIsNone(data["bio"])

    def _verify_private_profile_response(self, response):
        """
        Verify that only the public fields are returned for a private user's profile
        """
        data = response.data
        self.assertEqual(2, len(data))
        self.assertEqual(self.user.username, data["username"])
        self.assertIsNone(data["profile_image"])

    @ddt.data(
        ("client", "user"),
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_default_profile(self, api_client, username):
        """
        Test that any logged in user can get the main test user's public profile information.
        """
        client = self.login_client(api_client, username)
        self.create_mock_profile(self.user)
        response = self.send_get(client)
        self._verify_full_profile_response(response)

    @ddt.data(
        ("client", "user"),
        ("different_client", "different_user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_private_profile(self, api_client, requesting_username):
        """
        Test that private profile information is only available to the test user themselves.
        """
        client = self.login_client(api_client, requesting_username)

        # Verify that a user with a private profile only returns the public fields
        UserPreference.set_preference(self.user, PROFILE_VISIBILITY_PREF_KEY, PRIVATE_VISIBILITY)
        self.create_mock_profile(self.user)
        response = self.send_get(client)
        self._verify_private_profile_response(response)

        # Verify that only the public fields are returned if 'include_all' parameter is specified as false
        response = self.send_get(client, query_parameters='include_all=false')
        self._verify_private_profile_response(response)

        # Verify that all fields are returned for the user themselves if
        # the 'include_all' parameter is specified as true.
        response = self.send_get(client, query_parameters='include_all=true')
        if requesting_username == "user":
            self._verify_full_profile_response(response)
        else:
            self._verify_private_profile_response(response)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_profile_unknown_user(self, api_client, username):
        """
        Test that requesting a user who does not exist returns a 404.
        """
        client = self.login_client(api_client, username)
        response = client.get(reverse("profiles_api", kwargs={'username': "does_not_exist"}))
        self.assertEqual(404, response.status_code)
