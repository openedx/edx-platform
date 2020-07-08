import unittest
from uuid import uuid4
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from enterprise.models import EnterpriseCustomerIdentityProvider, EnterpriseCustomer
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
        self.enterprise_customer = EnterpriseCustomer.objects.create(uuid=ENTERPRISE_ID, name='test-ep', slug='test-ep')
        self.samlproviderconfig = SAMLProviderConfig.objects.create(
            entity_id=SINGLE_PROVIDER_CONFIG.entity_id,
            metadata_source=SINGLE_PROVIDER_CONFIG.metadata_source
        )
        self.enterprisecustomeridp = EnterpriseCustomerIdentityProvider.objects.create(
            provider_id=self.samlproviderconfig.id,
            enterprise_customer_id=ENTERPRISE_ID
        )
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_DASHBOARD_ROLE, str(ENTERPRISE_ID))])
        self.client.force_authenticate(user=self.user)

    def test_get_one_config_by_enterprise_uuid_found(self):
        # GET auth/saml/v0/providerconfig/{id}
        url = reverse('samlproviderconfig-detail', kwargs={'enterprise_customer_uuid', ENTERPRISE_ID})
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
