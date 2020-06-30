import unittest
from datetime import datetime
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from third_party_auth.tests import testutil
from third_party_auth.models import SAMLProviderData


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class SAMLProviderDataTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    def test_get_all_data(self):
        # auth/saml/v0/providerconfig/
        url = reverse('samlproviderdata-list')
        print(url)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderData.objects.count(), 0)

    def test_get_one_data_id_not_found(self):
        # auth/saml/v0/providerconfig/{id}
        url = reverse('samlproviderdata-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(SAMLProviderData.objects.count(), 0)

    def test_create_one_providerdata_success(self):
        # POST auth/saml/v0/providerdata/ -d data
        url = reverse('samlproviderdata-list')
        fetched_at = '2009-01-10 00:12:12'
        data = {
            'entity_id': 'http://saml.test.io',
            'sso_url': 'http://sso.saml.test.io',
            'fetched_at': fetched_at,
            'name': 'provider-1',
            'public_key': 'testkeyvalues'
        }
        self.assertEqual(SAMLProviderData.objects.count(), 0)
        response = self.client.post(url, data, format='json')
        print(response)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SAMLProviderData.objects.count(), 1)
        self.assertEqual(SAMLProviderData.objects.get().fetched_at.strftime('%Y-%m-%d %H:%M:%S'), fetched_at)

    def test_create_one_providerdata_fail(self):
        # POST auth/saml/v0/providerdata/ -d data
        url = reverse('samlproviderdata-list')
        data = {
            'name': 'provider-1'
        }
        self.assertEqual(SAMLProviderData.objects.count(), 0)
        response = self.client.post(url, data, format='json')
        print(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SAMLProviderData.objects.count(), 0)
