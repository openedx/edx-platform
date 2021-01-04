"""
Tests for SAMLProviderConfig endpoints
"""

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
from enterprise.constants import ENTERPRISE_ADMIN_ROLE, ENTERPRISE_LEARNER_ROLE
from common.djangoapps.third_party_auth.tests.samlutils import set_jwt_cookie
from common.djangoapps.third_party_auth.models import SAMLProviderConfig, SAMLConfiguration
from common.djangoapps.third_party_auth.tests import testutil
from common.djangoapps.third_party_auth.tests.utils import skip_unless_thirdpartyauth
from common.djangoapps.third_party_auth.utils import convert_saml_slug_provider_id

# country here refers to the URN provided by a user's IDP
SINGLE_PROVIDER_CONFIG = {
    'entity_id': 'id',
    'metadata_source': 'http://test.url',
    'name': 'name-of-config',
    'enabled': 'true',
    'slug': 'test-slug',
    'country': 'https://example.customer.com/countrycode',
}

SINGLE_PROVIDER_CONFIG_2 = copy.copy(SINGLE_PROVIDER_CONFIG)
SINGLE_PROVIDER_CONFIG_2['name'] = 'name-of-config-2'
SINGLE_PROVIDER_CONFIG_2['slug'] = 'test-slug-2'

SINGLE_PROVIDER_CONFIG_3 = copy.copy(SINGLE_PROVIDER_CONFIG)
SINGLE_PROVIDER_CONFIG_3['name'] = 'name-of-config-3'
SINGLE_PROVIDER_CONFIG_3['slug'] = 'test-slug-3'

ENTERPRISE_ID = str(uuid4())
ENTERPRISE_ID_NON_EXISTENT = str(uuid4())


@skip_unless_thirdpartyauth()
class SAMLProviderConfigTests(APITestCase):
    """
    API Tests for SAMLProviderConfig REST endpoints
    The skip annotation above exists because we currently cannot run this test in
    the cms mode in CI builds, where the third_party_auth application is not loaded
    """
    @classmethod
    def setUpTestData(cls):
        super(SAMLProviderConfigTests, cls).setUpTestData()
        cls.user = User.objects.create_user(username='testuser', password='testpwd')
        cls.site, _ = Site.objects.get_or_create(domain='example.com')
        cls.enterprise_customer = EnterpriseCustomer.objects.create(
            uuid=ENTERPRISE_ID,
            name='test-ep',
            slug='test-ep',
            site=cls.site)
        cls.samlproviderconfig, _ = SAMLProviderConfig.objects.get_or_create(
            entity_id=SINGLE_PROVIDER_CONFIG['entity_id'],
            metadata_source=SINGLE_PROVIDER_CONFIG['metadata_source'],
            slug=SINGLE_PROVIDER_CONFIG['slug'],
            country=SINGLE_PROVIDER_CONFIG['country'],
        )
        cls.samlconfiguration, _ = SAMLConfiguration.objects.get_or_create(
            enabled=True,
            site=cls.site,
            slug='edxSideTest',
        )

    def setUp(self):
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, ENTERPRISE_ID)])
        self.client.force_authenticate(user=self.user)

    def test_get_one_config_by_enterprise_uuid_found(self):
        """
        GET auth/saml/v0/provider_config/?enterprise_customer_uuid=id=id
        """

        # for GET to work, we need an association present
        EnterpriseCustomerIdentityProvider.objects.get_or_create(
            provider_id=convert_saml_slug_provider_id(self.samlproviderconfig.slug),
            enterprise_customer_id=ENTERPRISE_ID
        )
        urlbase = reverse('saml_provider_config-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['entity_id'], SINGLE_PROVIDER_CONFIG['entity_id'])
        self.assertEqual(results[0]['metadata_source'], SINGLE_PROVIDER_CONFIG['metadata_source'])
        self.assertEqual(response.data['results'][0]['country'], SINGLE_PROVIDER_CONFIG['country'])
        self.assertEqual(SAMLProviderConfig.objects.count(), 1)

    def test_get_one_config_by_enterprise_uuid_invalid_uuid(self):
        """
        GET auth/saml/v0/provider_config/?enterprise_customer_uuid=invalidUUID
        """
        urlbase = reverse('saml_provider_config-list')
        query_kwargs = {'enterprise_customer_uuid': 'invalid_uuid'}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_one_config_by_enterprise_uuid_not_found(self):
        """
        GET auth/saml/v0/provider_config/?enterprise_customer_uuid=valid-but-nonexistent-uuid
        """

        # the user must actually be authorized for this enterprise
        # since we are testing auth passes but association to samlproviderconfig is not found
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, ENTERPRISE_ID_NON_EXISTENT)])
        self.client.force_authenticate(user=self.user)

        urlbase = reverse('saml_provider_config-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID_NON_EXISTENT}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))
        orig_count = SAMLProviderConfig.objects.count()

        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(SAMLProviderConfig.objects.count(), orig_count)

    def test_create_one_config(self):
        """
        POST auth/saml/v0/provider_config/ -d data
        """
        url = reverse('saml_provider_config-list')
        data = copy.copy(SINGLE_PROVIDER_CONFIG_2)
        data['enterprise_customer_uuid'] = ENTERPRISE_ID
        orig_count = SAMLProviderConfig.objects.count()

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SAMLProviderConfig.objects.count(), orig_count + 1)
        provider_config = SAMLProviderConfig.objects.get(slug=SINGLE_PROVIDER_CONFIG_2['slug'])
        self.assertEqual(provider_config.name, 'name-of-config-2')
        self.assertEqual(provider_config.country, SINGLE_PROVIDER_CONFIG_2['country'])

        # check association has also been created
        self.assertTrue(
            EnterpriseCustomerIdentityProvider.objects.filter(
                provider_id=convert_saml_slug_provider_id(provider_config.slug)
            ).exists(),
            'Cannot find EnterpriseCustomer-->SAMLProviderConfig association'
        )

    def test_create_one_config_fail_non_existent_enterprise_uuid(self):
        """
        POST auth/saml/v0/provider_config/ -d data
        """
        url = reverse('saml_provider_config-list')
        data = copy.copy(SINGLE_PROVIDER_CONFIG_2)
        data['enterprise_customer_uuid'] = ENTERPRISE_ID_NON_EXISTENT
        orig_count = SAMLProviderConfig.objects.count()

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(SAMLProviderConfig.objects.count(), orig_count)

        # check association has NOT been created
        self.assertFalse(
            EnterpriseCustomerIdentityProvider.objects.filter(
                provider_id=convert_saml_slug_provider_id(SINGLE_PROVIDER_CONFIG_2['slug'])
            ).exists(),
            'Did not expect to find EnterpriseCustomer-->SAMLProviderConfig association'
        )

    def test_create_one_config_with_absent_enterprise_uuid(self):
        """
        POST auth/saml/v0/provider_config/ -d data
        """
        url = reverse('saml_provider_config-list')
        data = copy.copy(SINGLE_PROVIDER_CONFIG_2)
        orig_count = SAMLProviderConfig.objects.count()

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(SAMLProviderConfig.objects.count(), orig_count)

    def test_create_one_config_with_no_country_urn(self):
        """
        POST auth/saml/v0/provider_config/ -d data
        """
        url = reverse('saml_provider_config-list')
        provider_config_no_country = {
            'entity_id': 'id',
            'metadata_source': 'http://test.url',
            'name': 'name-of-config-no-country',
            'enabled': 'true',
            'slug': 'test-slug-none',
            'enterprise_customer_uuid': ENTERPRISE_ID,
        }

        response = self.client.post(url, provider_config_no_country)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        provider_config = SAMLProviderConfig.objects.get(slug='test-slug-none')
        self.assertEqual(provider_config.country, '')

    def test_create_one_config_with_empty_country_urn(self):
        """
        POST auth/saml/v0/provider_config/ -d data
        """
        url = reverse('saml_provider_config-list')
        provider_config_blank_country = {
            'entity_id': 'id',
            'metadata_source': 'http://test.url',
            'name': 'name-of-config-blank-country',
            'enabled': 'true',
            'slug': 'test-slug-empty',
            'enterprise_customer_uuid': ENTERPRISE_ID,
            'country': '',
        }

        response = self.client.post(url, provider_config_blank_country)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        provider_config = SAMLProviderConfig.objects.get(slug='test-slug-empty')
        self.assertEqual(provider_config.country, '')

    def test_unauthenticated_request_is_forbidden(self):
        self.client.logout()
        urlbase = reverse('saml_provider_config-list')
        query_kwargs = {'enterprise_customer_uuid': ENTERPRISE_ID}
        url = '{}?{}'.format(urlbase, urlencode(query_kwargs))
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_LEARNER_ROLE, ENTERPRISE_ID)])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.logout()
        set_jwt_cookie(self.client, self.user, [(ENTERPRISE_ADMIN_ROLE, ENTERPRISE_ID_NON_EXISTENT)])
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_one_config_with_samlconfiguration(self):
        """
        POST auth/saml/v0/provider_config/ -d data
        """
        url = reverse('saml_provider_config-list')
        data = copy.copy(SINGLE_PROVIDER_CONFIG_3)
        data['enterprise_customer_uuid'] = ENTERPRISE_ID
        data['saml_config_id'] = self.samlconfiguration.id

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        provider_config = SAMLProviderConfig.objects.get(slug=SINGLE_PROVIDER_CONFIG_3['slug'])
        self.assertEqual(provider_config.saml_configuration, self.samlconfiguration)
