"""
Very basic testing for appsembler.tpa_admin
"""

import pytest
from mock import patch
from rest_framework.reverse import reverse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.test import APITestCase

from third_party_auth.models import SAMLProviderConfig
from third_party_auth.tests.factories import SAMLConfigurationFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from student.tests.factories import UserFactory


VIEWS_MODULE = 'openedx.core.djangoapps.appsembler.tpa_admin.api'


class BaseViewTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.my_site = SiteFactory()
        self.other_site = SiteFactory()
        self.caller = UserFactory()
        self.client.login(username=self.caller.username, password=self.caller.password)


class BaseSAMLConfigurationTestCase(BaseViewTestCase):
    def setUp(self):
        super().setUp()
        self.my_saml_config = SAMLConfigurationFactory(site=self.my_site)
        self.other_saml_config = SAMLConfigurationFactory(site=self.other_site)
        assert self.my_saml_config != self.other_saml_config


@patch(VIEWS_MODULE + '.SAMLConfigurationViewSet.permission_classes', [AllowAny])
class SAMLConfigurationViewSetTests(BaseSAMLConfigurationTestCase):
    def setUp(self):
        super().setUp()

    def test_get_list(self):
        url = reverse('saml-configuration-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_get_filtered_by_site_id(self):
        url = reverse('saml-configuration-list')
        url += '?site_id={}'.format(self.my_site.id)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        found_site_ids = [rec['site'] for rec in results]
        assert self.other_site not in found_site_ids

    def test_get_detail(self):
        url = reverse('saml-configuration-detail', args=[self.my_saml_config.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.skip('Test not implemented')
    def test_create(self):
        pass

    @pytest.mark.skip('Test not implemented')
    def test_destroy(self):
        pass


class SAMLConfigurationSiteDetailTests(BaseSAMLConfigurationTestCase):
    """
    The view, as tested does not have any permissions directly associated
    The test is passing without patching permissions
    """
    def setUp(self):
        super().setUp()

    def test_get(self):
        url = reverse('site-saml-configuration', args=[self.my_site.id])
        response = self.client.get(url)
        data = response.json()
        assert response.status_code == status.HTTP_200_OK
        assert data['id'] == self.my_saml_config.id
        assert data['site'] == self.my_site.id


class BaseSAMLProviderConfigTestCase(BaseViewTestCase):
    def setUp(self):
        """
        We can't use SAMLProviderConfigFactory without modifying it because the
        following is True:

        ```
        spc_1 = SAMLProviderConfigFactory(site=self.my_site)
        spc_2 = SAMLProviderConfigFactory(site=self.other_site)
        assert spc_1 == spc_2
        ```
        """
        super().setUp()
        self.my_spc = SAMLProviderConfig.objects.create(
            site=self.my_site,
            name='SAML Alpha',
            slug='saml-alpha',
            entity_id='https://alpha.com/foo',
            metadata_source='https://alpha.com/foo-xml')
        self.other_spc = SAMLProviderConfig.objects.create(
            site=self.other_site,
            name='SAML Bravo',
            slug='saml-bravo',
            entity_id='https://bravo.com/foo',
            metadata_source='https://bravo.com/foo-xml')


@patch(VIEWS_MODULE + '.SAMLProviderConfigViewSet.permission_classes', [AllowAny])
class SAMLProviderConfigViewSetTests(BaseSAMLProviderConfigTestCase):
    def setUp(self):
        super().setUp()

    def test_get_list(self):
        url = reverse('saml-providers-config-list')
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']
        found_site_ids = [rec['site'] for rec in results]
        assert set([self.my_site.id, self.other_site.id]) == set(found_site_ids)

    def test_get_filtered_by_site_id(self):
        url = reverse('saml-providers-config-list')
        url += '?site_id={}'.format(self.my_site.id)
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = response.json()['results']

        found_site_ids = [rec['site'] for rec in results]
        assert self.other_site not in found_site_ids

    def test_get_detail(self):
        url = reverse('saml-providers-config-detail',
                      args=[self.my_spc.id])
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.skip('Test not implemented')
    def test_create(self):
        pass

    @pytest.mark.skip('Test not implemented')
    def test_destroy(self):
        pass


class SAMLProviderSiteDetailTests(BaseSAMLProviderConfigTestCase):
    """
    The view, as tested does not have any permissions directly associated
    The test is passing without patching permissions
    """
    def setUp(self):
        super().setUp()

    def test_get(self):
        url = reverse('site-saml-provider', args=[self.my_site.id])
        response = self.client.get(url)
        results = response.json()['results']
        assert response.status_code == status.HTTP_200_OK
        found_site_ids = [rec['site'] for rec in results]
        assert self.other_site not in found_site_ids
