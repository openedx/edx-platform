# -*- coding: utf-8 -*-
"""
Unit tests for profile APIs.
"""

import unittest
import ddt
import json
from datetime import datetime

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.conf import settings
from rest_framework.test import APITestCase, APIClient

from student.tests.factories import UserFactory
from student.models import UserProfile, PendingEmailChange
from student.views import confirm_email_change
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.accounts.tests.test_views import UserAPITestCase


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestPreferencesAPI(UserAPITestCase):
    """
    Unit tests /api/user/v0/accounts/{username}/
    """
    __test__ = True

    def setUp(self):
        super(TestPreferencesAPI, self).setUp()
        self.url_endpoint_name = "preferences_api"
        self.url = reverse(self.url_endpoint_name, kwargs={'username': self.user.username})

    def test_get_different_user(self):
        """
        Test that a client (logged in) cannot get the preferences information for a different client.
        """
        self.different_client.login(username=self.different_user.username, password=self.test_password)
        self.send_get(self.different_client, expected_status=404)

    def test_get_preferences_default(self):
        """
        Test that a client (logged in) can get her own preferences information (verifying the default
        state before any preferences are stored).
        """
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.send_get(self.client)
        self.assertEqual({}, response.data)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_preferences(self, api_client, user):
        """
        Test that a client (logged in) can get her own preferences information. Also verifies that a "is_staff"
        user can get the preferences information for other users.
        """
        # Create some test preferences values.
        UserPreference.set_preference(self.user, "dict_pref", {"int_key": 10})
        UserPreference.set_preference(self.user, "string_pref", "value")

        # Log in the client and do the GET.
        client = self.login_client(api_client, user)
        response = self.send_get(client)
        self.assertEqual({"dict_pref": "{'int_key': 10}", "string_pref": "value"}, response.data)


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestPreferencesDetailAPI(UserAPITestCase):
    """
    Unit tests /api/user/v0/accounts/{username}/{preference_key}
    """
    __test__ = True

    def setUp(self):
        super(TestPreferencesDetailAPI, self).setUp()
        self.test_pref_key = "test_key"
        self.test_pref_value = "test_value"
        UserPreference.set_preference(self.user, self.test_pref_key, self.test_pref_value)
        self.url_endpoint_name = "preferences_detail_api"
        self._set_url(self.test_pref_key)

    def _set_url(self, preference_key):
        self.url = reverse(
            self.url_endpoint_name,
            kwargs={'username': self.user.username, 'preference_key': preference_key}
        )

    def test_get_different_user(self):
        """
        Test that a client (logged in) cannot get the preferences information for a different client.
        """
        self.different_client.login(username=self.different_user.username, password=self.test_password)
        self.send_get(self.different_client, expected_status=404)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_unknown_user(self, api_client, username):
        """
        Test that requesting a user who does not exist returns a 404. Most override the base class
        implementation because it is necessary to specify "preference_key".
        """
        client = self.login_client(api_client, username)
        response = client.get(
            reverse(self.url_endpoint_name, kwargs={'username': "does_not_exist", 'preference_key': self.test_pref_key})
        )
        self.assertEqual(404, response.status_code)

    def test_get_preference_does_not_exist(self):
        """
        Test that a 404 is returned if the user does not have a preference with the given preference_key.
        """
        self._set_url("does_not_exist")
        self.client.login(username=self.user.username, password=self.test_password)
        response = self.send_get(self.client, expected_status=404)
        self.assertIsNone(response.data)

    @ddt.data(
        ("client", "user"),
        ("staff_client", "staff_user"),
    )
    @ddt.unpack
    def test_get_preference(self, api_client, user):
        """
        Test that a client (logged in) can get her own preferences information. Also verifies that a "is_staff"
        user can get the preferences information for other users.
        """
        client = self.login_client(api_client, user)
        response = self.send_get(client)
        self.assertEqual(self.test_pref_value, response.data)

        # Test a different value.
        UserPreference.set_preference(self.user, "dict_pref", {"int_key": 10})
        self._set_url("dict_pref")
        response = self.send_get(client)
        self.assertEqual("{'int_key': 10}", response.data)
