from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from third_party_auth.models import SAMLProviderConfig


class SAMLProviderConfigTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    def test_get_all_configs(self):
        # ^^auth/saml/v0/providerconfig/
        url = reverse('samlproviderconfig-list')
        print(url)
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderConfig.objects.count(), 0)

    def test_get_one_config_id_not_found(self):
        # ^^auth/saml/v0/providerconfig/{id}
        url = reverse('samlproviderconfig-detail', args=[1])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(SAMLProviderConfig.objects.count(), 0)
