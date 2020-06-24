from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from third_party_auth.models import SAMLProviderData

class SAMLProviderDataTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    def test_get_single_providerdata(self):
        # ^^auth/saml/v0/providerdata/
        url = reverse('samlproviderdata-detail', args=['1'])
        response = self.client.get(url, format='json')
        # only admin user has access, as of now
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderData.objects.count(), 1)
