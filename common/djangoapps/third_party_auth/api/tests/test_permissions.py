"""
Tests for the Third Party Auth permissions
"""
import unittest
import ddt
from mock import Mock

from rest_framework.test import APITestCase
from django.conf import settings
from third_party_auth.api.permissions import ThirdPartyAuthProviderApiPermission

from third_party_auth.tests.testutil import ThirdPartyAuthTestMixin

IDP_SLUG_TESTSHIB = 'testshib'
PROVIDER_ID_TESTSHIB = 'saml-' + IDP_SLUG_TESTSHIB


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class ThirdPartyAuthApiPermissionTest(ThirdPartyAuthTestMixin, APITestCase):
    """ Tests for third party auth API permission """
    def setUp(self):
        """ Create users and oauth client for use in the tests """
        super(ThirdPartyAuthApiPermissionTest, self).setUp()

        client = self.configure_oauth_client()
        self.configure_api_permission(client, PROVIDER_ID_TESTSHIB)

    @ddt.data(
        (1, PROVIDER_ID_TESTSHIB, True),
        (1, 'invalid-provider-id', False),
        (999, PROVIDER_ID_TESTSHIB, False),
        (999, 'invalid-provider-id', False),
        (1, None, False),
    )
    @ddt.unpack
    def test_api_permission(self, client_pk, provider_id, expect):
        request = Mock()
        request.auth = Mock()
        request.auth.client_id = client_pk

        result = ThirdPartyAuthProviderApiPermission(provider_id).has_permission(request, None)
        self.assertEqual(result, expect)

    def test_api_permission_unauthorized_client(self):
        client = self.configure_oauth_client()
        self.configure_api_permission(client, 'saml-anotherprovider')

        request = Mock()
        request.auth = Mock()
        request.auth.client_id = client.pk

        result = ThirdPartyAuthProviderApiPermission(PROVIDER_ID_TESTSHIB).has_permission(request, None)
        self.assertEqual(result, False)
