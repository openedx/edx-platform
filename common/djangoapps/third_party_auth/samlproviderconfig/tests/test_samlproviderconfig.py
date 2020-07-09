import unittest
from uuid import uuid4
from django.urls import reverse
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase

from enterprise.models import EnterpriseCustomerIdentityProvider, EnterpriseCustomer
from enterprise.constants import ENTERPRISE_ADMIN_ROLE
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

ENTERPRISE_ID = uuid4()


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class SAMLProviderConfigTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpwd')
        self.site, _ = Site.objects.get_or_create(domain='example.com')
        self.enterprise_customer = EnterpriseCustomer.objects.create(
            uuid=ENTERPRISE_ID,
            name='test-ep',
            slug='test-ep',
            site=self.site)
        self.samlproviderconfig = SAMLProviderConfig.objects.create(
            entity_id=SINGLE_PROVIDER_CONFIG['entity_id'],
            metadata_source=SINGLE_PROVIDER_CONFIG['metadata_source']
        )
        self.enterprisecustomeridp = EnterpriseCustomerIdentityProvider.objects.create(
            provider_id=self.samlproviderconfig.id,
            enterprise_customer_id=ENTERPRISE_ID
        )
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, str(ENTERPRISE_ID))])
        self.client.force_authenticate(user=self.user)

    def test_get_one_config_by_enterprise_uuid_found(self):
        # GET auth/saml/v0/providerconfig/{id}
        urlbase = reverse('samlproviderconfig-list')
        query_kwargs = {'enterprise_customer_uuid': str(ENTERPRISE_ID)}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderConfig.objects.count(), 1)
