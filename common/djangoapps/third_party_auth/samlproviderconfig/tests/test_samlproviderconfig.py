import unittest
from uuid import uuid4
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from third_party_auth.samlutils.utils import set_jwt_cookie

from third_party_auth.models import SAMLProviderConfig
from third_party_auth.tests import testutil

SINGLE_PROVIDER_CONFIG = {
    'entity_id': 'id',
    'metadata_source': 'http://test.url',
    'name': 'name-of-config',
    'enabled': 'true',
    'slug': 'test-slug'
}

ENTERPRISE_ADMIN_DASHBOARD_ROLE = 'enterprise.can_access_admin_dashboard'
ENTERPRISE_ID = uuid4()


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class SAMLProviderConfigTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpwd')
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_DASHBOARD_ROLE, str(ENTERPRISE_ID))])
        self.client.force_authenticate(user=self.user)

    def test_get_all_configs(self):
        # ^auth/saml/v0/providerconfig/
        url = reverse('samlproviderconfig-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderConfig.objects.count(), 0)

    def test_get_one_config_id_not_found(self):
        # GET auth/saml/v0/providerconfig/{id}
        url = reverse('samlproviderconfig-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(SAMLProviderConfig.objects.count(), 0)

    def test_create_one_config(self):
        # POST auth/saml/v0/providerconfig/ -d data
        url = reverse('samlproviderconfig-list')
        data = SINGLE_PROVIDER_CONFIG
        self.assertEqual(SAMLProviderConfig.objects.count(), 0)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SAMLProviderConfig.objects.count(), 1)
        providerconfig = SAMLProviderConfig.objects.get()
        self.assertEqual(providerconfig.slug, 'test-slug')
        self.assertEqual(providerconfig.name, 'name-of-config')

    '''def test_update_one_config(self):
        # Patch auth/saml/v0/providerconfig/{id}/ -d data

        # first create a config
        url = reverse('samlproviderconfig-list')
        data = SINGLE_PROVIDER_CONFIG
        response = self.client.post(url, data, format='json')
        providerconfig = SAMLProviderConfig.objects.get()
        self.assertEqual(providerconfig.enabled, True)

        # now test the patch works
        url = reverse('samlproviderconfig-detail', args=[1])
        data = {
            'enabled': 'false',
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderConfig.objects.count(), 1)
        providerconfig = SAMLProviderConfig.objects.get()
        self.assertEqual(providerconfig.enabled, False)
    '''
