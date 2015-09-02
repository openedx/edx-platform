"""
Tests for the Third Party Auth REST API
"""
import json
import unittest

import ddt
from mock import patch
from django.test import Client
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from django.test.utils import override_settings

from util.testing import UrlResetMixin
from openedx.core.lib.django_test_client_utils import get_absolute_url
from social.apps.django_app.default.models import UserSocialAuth
from student.tests.factories import UserFactory
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin


VALID_API_KEY = "i am a key"


@override_settings(EDX_API_KEY=VALID_API_KEY)
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ThirdPartyAuthAPITests(ThirdPartyAuthTestMixin, APITestCase):
    """
    Test the Third Party Auth REST API
    """
    ALICE_USERNAME = "alice"
    CARL_USERNAME = "carl"
    STAFF_USERNAME = "staff"
    ADMIN_USERNAME = "admin"
    # These users will be created and linked to third party accounts:
    LINKED_USERS = (ALICE_USERNAME, STAFF_USERNAME, ADMIN_USERNAME)
    PASSWORD = "edx"

    def setUp(self):
        """ Create users for use in the tests """
        super(ThirdPartyAuthAPITests, self).setUp()

        google = self.configure_google_provider(enabled=True)
        self.configure_facebook_provider(enabled=True)
        self.configure_linkedin_provider(enabled=False)
        self.enable_saml()
        testshib = self.configure_saml_provider(name='TestShib', enabled=True, idp_slug='testshib')

        # Create several users and link each user to Google and TestShib
        for username in self.LINKED_USERS:
            make_superuser = (username == self.ADMIN_USERNAME)
            make_staff = (username == self.STAFF_USERNAME) or make_superuser
            user = UserFactory.create(
                username=username,
                password=self.PASSWORD,
                is_staff=make_staff,
                is_superuser=make_superuser
            )
            UserSocialAuth.objects.create(
                user=user,
                provider=google.backend_name,
                uid='{}@gmail.com'.format(username),
            )
            UserSocialAuth.objects.create(
                user=user,
                provider=testshib.backend_name,
                uid='{}:{}'.format(testshib.idp_slug, username),
            )
        # Create another user not linked to any providers:
        UserFactory.create(username=self.CARL_USERNAME, password=self.PASSWORD)

    def expected_active(self, username):
        """ The JSON active providers list response expected for the given user """
        if username not in self.LINKED_USERS:
            return []
        return [
            {
                "provider_id": "oa2-google-oauth2",
                "name": "Google",
                "remote_id": "{}@gmail.com".format(username),
            },
            {
                "provider_id": "saml-testshib",
                "name": "TestShib",
                # The "testshib:" prefix is stored in the UserSocialAuth.uid field but should
                # not be present in the 'remote_id', since that's an implementation detail:
                "remote_id": username,
            },
        ]

    @ddt.data(
        # Any user can query their own list of providers
        (ALICE_USERNAME, ALICE_USERNAME, 200),
        (CARL_USERNAME, CARL_USERNAME, 200),
        # A regular user cannot query another user nor deduce the existence of users based on the status code
        (ALICE_USERNAME, STAFF_USERNAME, 403),
        (ALICE_USERNAME, "nonexistent_user", 403),
        # Even Staff cannot query other users
        (STAFF_USERNAME, ALICE_USERNAME, 403),
        # But admins can
        (ADMIN_USERNAME, ALICE_USERNAME, 200),
        (ADMIN_USERNAME, CARL_USERNAME, 200),
        (ADMIN_USERNAME, "invalid_username", 404),
    )
    @ddt.unpack
    def test_list_connected_providers(self, request_user, target_user, expect_result):
        self.client.login(username=request_user, password=self.PASSWORD)
        url = reverse('third_party_auth_users_api', kwargs={'username': target_user})

        response = self.client.get(url)
        self.assertEqual(response.status_code, expect_result)
        if expect_result == 200:
            self.assertIn("active", response.data)
            self.assertItemsEqual(response.data["active"], self.expected_active(target_user))

    @ddt.data(
        # A server with a valid API key can query any user's list of providers
        (VALID_API_KEY, ALICE_USERNAME, 200),
        (VALID_API_KEY, "invalid_username", 404),
        ("i am an invalid key", ALICE_USERNAME, 403),
        (None, ALICE_USERNAME, 403),
    )
    @ddt.unpack
    def test_list_connected_providers__withapi_key(self, api_key, target_user, expect_result):
        url = reverse('third_party_auth_users_api', kwargs={'username': target_user})
        response = self.client.get(url, HTTP_X_EDX_API_KEY=api_key)
        self.assertEqual(response.status_code, expect_result)
        if expect_result == 200:
            self.assertIn("active", response.data)
            self.assertItemsEqual(response.data["active"], self.expected_active(target_user))
