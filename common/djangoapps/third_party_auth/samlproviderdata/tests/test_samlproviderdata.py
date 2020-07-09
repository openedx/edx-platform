import unittest
import copy
import pytz
from uuid import uuid4
from datetime import datetime
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.http import urlencode
from rest_framework import status
from rest_framework.test import APITestCase

from enterprise.models import EnterpriseCustomer, EnterpriseCustomerIdentityProvider
from enterprise.constants import ENTERPRISE_ADMIN_ROLE

from third_party_auth.tests import testutil
from third_party_auth.models import SAMLProviderData, SAMLProviderConfig
from third_party_auth.samlutils.utils import set_jwt_cookie

SINGLE_PROVIDER_CONFIG = {
    'entity_id': 'http://entity-id-1',
    'metadata_source': 'http://test.url',
    'name': 'name-of-config',
    'enabled': 'true',
    'slug': 'test-slug'
}

# entity_id here matches that of the providerconfig, intentionally
# that allows this data entity to be found
SINGLE_DATA_CONFIG = {
    'entity_id': 'http://entity-id-1',
    'sso_url': 'http://test.url',
    'public_key': 'a-key0Aid98',
    'fetched_at': datetime.now(pytz.UTC).replace(microsecond=0)
}

SINGLE_DATA_CONFIG_2 = copy.copy(SINGLE_DATA_CONFIG)
SINGLE_DATA_CONFIG_2['entity_id'] = 'http://entity-id-2'
SINGLE_DATA_CONFIG_2['sso_url'] = 'http://test2.url'

ENTERPRISE_ID = str(uuid4())


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, testutil.AUTH_FEATURES_KEY + ' not enabled')
class SAMLProviderDataTests(APITestCase):
    """
        API Tests for SAMLProviderConfig REST endpoints
    """
    @classmethod
    def setUpTestData(cls):
        super(SAMLProviderDataTests, cls).setUpTestData()
        cls.user = User.objects.create_user(username='testuser', password='testpwd')
        cls.site, _ = Site.objects.get_or_create(domain='example.com')
        cls.enterprise_customer = EnterpriseCustomer.objects.create(
            uuid=ENTERPRISE_ID,
            name='test-ep',
            slug='test-ep',
            site=cls.site)
        cls.samlproviderconfig, _ = SAMLProviderConfig.objects.get_or_create(
            entity_id=SINGLE_PROVIDER_CONFIG['entity_id'],
            metadata_source=SINGLE_PROVIDER_CONFIG['metadata_source']
        )
        # the entity_id here must match that of the samlproviderconfig
        cls.samlproviderdata, _ = SAMLProviderData.objects.get_or_create(
            entity_id=SINGLE_DATA_CONFIG['entity_id'],
            sso_url=SINGLE_DATA_CONFIG['sso_url'],
            fetched_at=SINGLE_DATA_CONFIG['fetched_at']
        )
        cls.enterprisecustomeridp, _ = EnterpriseCustomerIdentityProvider.objects.get_or_create(
            provider_id=cls.samlproviderconfig.id,
            enterprise_customer_id=ENTERPRISE_ID
        )

    def setUp(self):
        # a cookie with roles: [{enterprise_admin_role: ent_id}] will be
        # needed to rbac to authorize access for this view
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, ENTERPRISE_ID)])
        self.client.force_authenticate(user=self.user)

    def test_get_one_providedata_success(self):
        # GET auth/saml/v0/providerdata/?enterprise_customer_uuid=id
        urlbase = reverse('samlproviderdata-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_one_providerdata_success(self):
        # POST auth/saml/v0/providerdata/?enterprise_customer_uuid -d data
        urlbase = reverse('samlproviderdata-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))
        fetched_at = '2009-01-10 00:12:12'
        data = SINGLE_DATA_CONFIG_2
        orig_count = SAMLProviderData.objects.count()
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SAMLProviderData.objects.count(), orig_count + 1)
        self.assertEqual(
            SAMLProviderData.objects.get(entity_id=SINGLE_DATA_CONFIG_2['entity_id']).sso_url,
            SINGLE_DATA_CONFIG_2['sso_url']
        )
