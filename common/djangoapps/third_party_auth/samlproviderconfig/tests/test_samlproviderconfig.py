import unittest
import copy
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

SINGLE_PROVIDER_CONFIG_2 = copy.copy(SINGLE_PROVIDER_CONFIG)
SINGLE_PROVIDER_CONFIG_2['name'] = 'name-of-config-2'
SINGLE_PROVIDER_CONFIG_2['slug'] = 'test-slug-2'

ENTERPRISE_ID = str(uuid4())


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
        self.samlproviderconfig, _ = SAMLProviderConfig.objects.get_or_create(
            entity_id=SINGLE_PROVIDER_CONFIG['entity_id'],
            metadata_source=SINGLE_PROVIDER_CONFIG['metadata_source']
        )
        self.enterprisecustomeridp, _ = EnterpriseCustomerIdentityProvider.objects.get_or_create(
            provider_id=self.samlproviderconfig.id,
            enterprise_customer_id=ENTERPRISE_ID
        )
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, ENTERPRISE_ID)])
        self.client.force_authenticate(user=self.user)

    def test_get_one_config_by_enterprise_uuid_found(self):
        # GET auth/saml/v0/providerconfig/?enterprise_customer_uuid=id=id
        urlbase = reverse('samlproviderconfig-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderConfig.objects.count(), 1)

    def test_create_one_config(self):
        # POST auth/saml/v0/providerconfig/?enterprise_customer_uuid=id -d data
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(reverse('samlproviderconfig-list'), urlencode(query_kwargs))
        data = SINGLE_PROVIDER_CONFIG_2
        orig_count = SAMLProviderConfig.objects.count()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SAMLProviderConfig.objects.count(), orig_count + 1)
        providerconfig = SAMLProviderConfig.objects.get(slug=SINGLE_PROVIDER_CONFIG_2['slug'])
        self.assertEqual(providerconfig.name, 'name-of-config-2')
