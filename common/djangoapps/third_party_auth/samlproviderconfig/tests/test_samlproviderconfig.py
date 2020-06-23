from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from third_party_auth.models import SAMLProviderConfig

class SAMLProviderConfigTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    def test_endpoint_authenticated(self):
        # ^^auth/samlproviderconfig/(?P<pk>[^/.]+)/$ [name='samlproviderconfig']
        url = reverse('samlproviderconfig', kwargs={'config_id':1})
        print(url)
        response = self.client.get(url, format='json')
        # only admin user has access, as of now
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SAMLProviderConfig.objects.count(), 0)
