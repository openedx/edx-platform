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
from enterprise.constants import ENTERPRISE_ADMIN_ROLE, ENTERPRISE_LEARNER_ROLE

from common.djangoapps.third_party_auth.tests import testutil
from common.djangoapps.third_party_auth.models import SAMLProviderData, SAMLProviderConfig
from common.djangoapps.third_party_auth.tests.samlutils import set_jwt_cookie
from common.djangoapps.third_party_auth.tests.utils import skip_unless_thirdpartyauth
from common.djangoapps.third_party_auth.utils import convert_saml_slug_provider_id

SINGLE_PROVIDER_CONFIG = {
    'entity_id': 'http://entity-id-1',
    'metadata_source': 'http://test.url',
    'name': 'name-of-config',
    'enabled': 'true',
    'slug': 'test-slug'
}

# entity_id here matches that of the providerconfig, intentionally
# that allows this data entity to be found
SINGLE_PROVIDER_DATA = {
    'entity_id': 'http://entity-id-1',
    'sso_url': 'http://test.url',
    'public_key': 'a-key0Aid98',
    'fetched_at': datetime.now(pytz.UTC).replace(microsecond=0)
}

SINGLE_PROVIDER_DATA_2 = copy.copy(SINGLE_PROVIDER_DATA)
SINGLE_PROVIDER_DATA_2['entity_id'] = 'http://entity-id-2'
SINGLE_PROVIDER_DATA_2['sso_url'] = 'http://test2.url'

ENTERPRISE_ID = str(uuid4())
BAD_ENTERPRISE_ID = str(uuid4())


@skip_unless_thirdpartyauth()
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
        cls.saml_provider_config, _ = SAMLProviderConfig.objects.get_or_create(
            entity_id=SINGLE_PROVIDER_CONFIG['entity_id'],
            metadata_source=SINGLE_PROVIDER_CONFIG['metadata_source']
        )
        # the entity_id here must match that of the saml_provider_config
        cls.saml_provider_data, _ = SAMLProviderData.objects.get_or_create(
            entity_id=SINGLE_PROVIDER_DATA['entity_id'],
            sso_url=SINGLE_PROVIDER_DATA['sso_url'],
            fetched_at=SINGLE_PROVIDER_DATA['fetched_at']
        )
        cls.enterprise_customer_idp, _ = EnterpriseCustomerIdentityProvider.objects.get_or_create(
            provider_id=convert_saml_slug_provider_id(cls.saml_provider_config.slug),
            enterprise_customer_id=ENTERPRISE_ID
        )

    def setUp(self):
        # a cookie with roles: [{enterprise_admin_role: ent_id}] will be
        # needed to rbac to authorize access for this view
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, ENTERPRISE_ID)])
        self.client.force_authenticate(user=self.user)

    def test_get_one_provider_data_success(self):
        # GET auth/saml/v0/providerdata/?enterprise_customer_uuid=id
        url_base = reverse('saml_provider_data-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(url_base, urlencode(query_kwargs))

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['sso_url'], SINGLE_PROVIDER_DATA['sso_url'])

    def test_create_one_provider_data_success(self):
        # POST auth/saml/v0/providerdata/ -d data
        url = reverse('saml_provider_data-list')
        data = copy.copy(SINGLE_PROVIDER_DATA_2)
        data['enterprise_customer_uuid'] = ENTERPRISE_ID
        orig_count = SAMLProviderData.objects.count()

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SAMLProviderData.objects.count(), orig_count + 1)
        self.assertEqual(
            SAMLProviderData.objects.get(entity_id=SINGLE_PROVIDER_DATA_2['entity_id']).sso_url,
            SINGLE_PROVIDER_DATA_2['sso_url']
        )

    def test_create_one_data_with_absent_enterprise_uuid(self):
        """
        POST auth/saml/v0/provider_data/ -d data
        """
        url = reverse('saml_provider_data-list')
        data = copy.copy(SINGLE_PROVIDER_DATA_2)
        orig_count = SAMLProviderData.objects.count()

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SAMLProviderData.objects.count(), orig_count)

    def test_patch_one_provider_data(self):
        # PATCH auth/saml/v0/providerdata/ -d data
        url = reverse('saml_provider_data-detail', kwargs={'pk': self.saml_provider_data.id})
        data = {
            'sso_url': 'http://new.url'
        }
        data['enterprise_customer_uuid'] = ENTERPRISE_ID
        orig_count = SAMLProviderData.objects.count()

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SAMLProviderData.objects.count(), orig_count)

        # ensure only the sso_url was updated
        fetched_provider_data = SAMLProviderData.objects.get(pk=self.saml_provider_data.id)
        self.assertEqual(fetched_provider_data.sso_url, 'http://new.url')
        self.assertEqual(fetched_provider_data.fetched_at, SINGLE_PROVIDER_DATA['fetched_at'])
        self.assertEqual(fetched_provider_data.entity_id, SINGLE_PROVIDER_DATA['entity_id'])

    def test_delete_one_provider_data(self):
        # DELETE auth/saml/v0/providerdata/ -d data
        url_base = reverse('saml_provider_data-detail', kwargs={'pk': self.saml_provider_data.id})
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(url_base, urlencode(query_kwargs))
        orig_count = SAMLProviderData.objects.count()

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SAMLProviderData.objects.count(), orig_count - 1)

        # ensure only the sso_url was updated
        query_set_count = SAMLProviderData.objects.filter(pk=self.saml_provider_data.id).count()
        self.assertEqual(query_set_count, 0)

    def test_get_one_provider_data_failure(self):
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, BAD_ENTERPRISE_ID)])
        self.client.force_authenticate(user=self.user)
        url_base = reverse('saml_provider_data-list')
        query_kwargs = {'enterprise_customer_uuid': BAD_ENTERPRISE_ID}
        url = '{}?{}'.format(url_base, urlencode(query_kwargs))

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_request_is_forbidden(self):
        self.client.logout()
        urlbase = reverse('saml_provider_data-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_LEARNER_ROLE, ENTERPRISE_ID)])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # manually running second case as DDT is having issues.
        self.client.logout()
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, BAD_ENTERPRISE_ID)])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
