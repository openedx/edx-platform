import unittest

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from third_party_auth.models import SAMLProviderConfig

class SAMLProviderConfigTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    def test_fetch_one_config(self):
        # ^^auth/samlproviderconfig/(?P<pk>[^/.]+)/$ [name='samlproviderconfig-detail']
        url = reverse('samlproviderconfig-detail')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderConfig.objects.count(), 1)
