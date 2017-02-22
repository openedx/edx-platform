# pylint: disable=no-member
"""
Tests for the Third Party Auth REST API
"""
import unittest

import ddt
from django.core.urlresolvers import reverse
from django.http import QueryDict
from mock import patch
from provider.constants import CONFIDENTIAL
from provider.oauth2.models import Client, AccessToken
from openedx.core.lib.api.permissions import ApiKeyHeaderPermission
from rest_framework.test import APITestCase
from django.conf import settings
from django.test.utils import override_settings
from social.apps.django_app.default.models import UserSocialAuth

from student.tests.factories import UserFactory
from third_party_auth.api.permissions import ThirdPartyAuthProviderApiPermission
from third_party_auth.models import ProviderApiPermissions
from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin


VALID_API_KEY = "i am a key"
IDP_SLUG_TESTSHIB = 'testshib'
PROVIDER_ID_TESTSHIB = 'saml-' + IDP_SLUG_TESTSHIB

ALICE_USERNAME = "alice"
CARL_USERNAME = "carl"
STAFF_USERNAME = "staff"
ADMIN_USERNAME = "admin"
# These users will be created and linked to third party accounts:
LINKED_USERS = (ALICE_USERNAME, STAFF_USERNAME, ADMIN_USERNAME)
PASSWORD = "edx"


def get_mapping_data_by_usernames(usernames):
    """ Generate mapping data used in response """
    return [{'username': username, 'remote_id': 'remote_' + username} for username in usernames]


class TpaAPITestCase(ThirdPartyAuthTestMixin, APITestCase):
    """ Base test class """

    def setUp(self):
        """ Create users for use in the tests """
        super(TpaAPITestCase, self).setUp()

        google = self.configure_google_provider(enabled=True)
        self.configure_facebook_provider(enabled=True)
        self.configure_linkedin_provider(enabled=False)
        self.enable_saml()
        testshib = self.configure_saml_provider(
            name='TestShib',
            enabled=True,
            idp_slug=IDP_SLUG_TESTSHIB
        )

        # Create several users and link each user to Google and TestShib
        for username in LINKED_USERS:
            make_superuser = (username == ADMIN_USERNAME)
            make_staff = (username == STAFF_USERNAME) or make_superuser
            user = UserFactory.create(
                username=username,
                password=PASSWORD,
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
                uid='{}:remote_{}'.format(testshib.idp_slug, username),
            )
        # Create another user not linked to any providers:
        UserFactory.create(username=CARL_USERNAME, password=PASSWORD)


@override_settings(EDX_API_KEY=VALID_API_KEY)
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class UserViewAPITests(TpaAPITestCase):
    """
    Test the Third Party Auth User REST API
    """

    def expected_active(self, username):
        """ The JSON active providers list response expected for the given user """
        if username not in LINKED_USERS:
            return []
        return [
            {
                "provider_id": "oa2-google-oauth2",
                "name": "Google",
                "remote_id": "{}@gmail.com".format(username),
            },
            {
                "provider_id": PROVIDER_ID_TESTSHIB,
                "name": "TestShib",
                # The "testshib:" prefix is stored in the UserSocialAuth.uid field but should
                # not be present in the 'remote_id', since that's an implementation detail:
                "remote_id": 'remote_' + username,
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
        self.client.login(username=request_user, password=PASSWORD)
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


@override_settings(EDX_API_KEY=VALID_API_KEY)
@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class UserMappingViewAPITests(TpaAPITestCase):
    """
    Test the Third Party Auth User Mapping REST API
    """
    @ddt.data(
        (VALID_API_KEY, PROVIDER_ID_TESTSHIB, 200, get_mapping_data_by_usernames(LINKED_USERS)),
        ("i am an invalid key", PROVIDER_ID_TESTSHIB, 403, None),
        (None, PROVIDER_ID_TESTSHIB, 403, None),
        (VALID_API_KEY, 'non-existing-id', 404, []),
    )
    @ddt.unpack
    def test_list_all_user_mappings_withapi_key(self, api_key, provider_id, expect_code, expect_data):
        url = reverse('third_party_auth_user_mapping_api', kwargs={'provider_id': provider_id})
        response = self.client.get(url, HTTP_X_EDX_API_KEY=api_key)
        self._verify_response(response, expect_code, expect_data)

    @ddt.data(
        (PROVIDER_ID_TESTSHIB, 'valid-token', 200, get_mapping_data_by_usernames(LINKED_USERS)),
        ('non-existing-id', 'valid-token', 404, []),
        (PROVIDER_ID_TESTSHIB, 'invalid-token', 401, []),
    )
    @ddt.unpack
    def test_list_all_user_mappings_oauth2(self, provider_id, access_token, expect_code, expect_data):
        url = reverse('third_party_auth_user_mapping_api', kwargs={'provider_id': provider_id})
        # create oauth2 auth data
        user = UserFactory.create(username='api_user')
        client = Client.objects.create(name='oauth2_client', client_type=CONFIDENTIAL)
        token = AccessToken.objects.create(user=user, client=client)
        ProviderApiPermissions.objects.create(client=client, provider_id=provider_id)

        if access_token == 'valid-token':
            access_token = token.token

        response = self.client.get(url, HTTP_AUTHORIZATION='Bearer {}'.format(access_token))
        self._verify_response(response, expect_code, expect_data)

    @ddt.data(
        ({'username': [ALICE_USERNAME, STAFF_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
        ({'remote_id': ['remote_' + ALICE_USERNAME, 'remote_' + STAFF_USERNAME, 'remote_' + CARL_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
        ({'username': [ALICE_USERNAME, CARL_USERNAME, STAFF_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
        ({'username': [ALICE_USERNAME], 'remote_id': ['remote_' + STAFF_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
    )
    @ddt.unpack
    def test_user_mappings_with_query_params_comma_separated(self, query_params, expect_code, expect_data):
        """ test queries like username=user1,user2,... """
        base_url = reverse(
            'third_party_auth_user_mapping_api', kwargs={'provider_id': PROVIDER_ID_TESTSHIB}
        )
        params = []
        for attr in ['username', 'remote_id']:
            if attr in query_params:
                params.append('{}={}'.format(attr, ','.join(query_params[attr])))
        url = "{}?{}".format(base_url, '&'.join(params))
        response = self.client.get(url, HTTP_X_EDX_API_KEY=VALID_API_KEY)
        self._verify_response(response, expect_code, expect_data)

    @ddt.data(
        ({'username': [ALICE_USERNAME, STAFF_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
        ({'remote_id': ['remote_' + ALICE_USERNAME, 'remote_' + STAFF_USERNAME, 'remote_' + CARL_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
        ({'username': [ALICE_USERNAME, CARL_USERNAME, STAFF_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
        ({'username': [ALICE_USERNAME], 'remote_id': ['remote_' + STAFF_USERNAME]}, 200,
         get_mapping_data_by_usernames([ALICE_USERNAME, STAFF_USERNAME])),
    )
    @ddt.unpack
    def test_user_mappings_with_query_params_multi_value_key(self, query_params, expect_code, expect_data):
        """ test queries like username=user1&username=user2&... """
        base_url = reverse(
            'third_party_auth_user_mapping_api', kwargs={'provider_id': PROVIDER_ID_TESTSHIB}
        )
        params = QueryDict('', mutable=True)
        for attr in ['username', 'remote_id']:
            if attr in query_params:
                params.setlist(attr, query_params[attr])
        url = "{}?{}".format(base_url, params.urlencode())
        response = self.client.get(url, HTTP_X_EDX_API_KEY=VALID_API_KEY)
        self._verify_response(response, expect_code, expect_data)

    def test_user_mappings_only_return_requested_idp_mapping_by_provider_id(self):
        testshib2 = self.configure_saml_provider(name='TestShib2', enabled=True, idp_slug='testshib2')
        username = 'testshib2user'
        user = UserFactory.create(
            username=username,
            password=PASSWORD,
            is_staff=False,
            is_superuser=False
        )
        UserSocialAuth.objects.create(
            user=user,
            provider=testshib2.backend_name,
            uid='{}:{}'.format(testshib2.idp_slug, username),
        )

        url = reverse('third_party_auth_user_mapping_api', kwargs={'provider_id': PROVIDER_ID_TESTSHIB})
        response = self.client.get(url, HTTP_X_EDX_API_KEY=VALID_API_KEY)
        self.assertEqual(response.status_code, 200)
        self._verify_response(response, 200, get_mapping_data_by_usernames(LINKED_USERS))

    @ddt.data(
        (True, True, 200),
        (False, True, 200),
        (True, False, 200),
        (False, False, 403)
    )
    @ddt.unpack
    def test_user_mapping_permission_logic(self, api_key_permission, token_permission, expect):
        url = reverse('third_party_auth_user_mapping_api', kwargs={'provider_id': PROVIDER_ID_TESTSHIB})
        with patch.object(ApiKeyHeaderPermission, 'has_permission', return_value=api_key_permission):
            with patch.object(ThirdPartyAuthProviderApiPermission, 'has_permission', return_value=token_permission):
                response = self.client.get(url)
                self.assertEqual(response.status_code, expect)

    def _verify_response(self, response, expect_code, expect_result):
        """ verify the items in data_list exists in response and data_results matches results in response """
        self.assertEqual(response.status_code, expect_code)
        if expect_code == 200:
            for item in ['results', 'count', 'num_pages']:
                self.assertIn(item, response.data)
            self.assertItemsEqual(response.data['results'], expect_result)
