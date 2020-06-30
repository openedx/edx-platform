import unittest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from third_party_auth.models import SAMLProviderConfig
from third_party_auth.tests import testutil


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class SAMLProviderConfigTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
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
        data = {
            'entity_id': 'id',
            'metadata_source': 'http://test.url',
            'name': 'name',
            'enabled': 'true',
            'slug': 'test-slug'
        }
        self.assertEqual(SAMLProviderConfig.objects.count(), 0)
        response = self.client.post(url, data, format='json')
        print(response)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SAMLProviderConfig.objects.count(), 1)
        self.assertEqual(SAMLProviderConfig.objects.get().slug, 'test-slug')
