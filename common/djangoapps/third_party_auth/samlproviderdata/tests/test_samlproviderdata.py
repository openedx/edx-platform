import unittest
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
