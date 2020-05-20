"""Tests covering the Organizations listing on the Studio home."""
import logging

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from mock import patch
from testfixtures import LogCapture
from waffle.testutils import override_switch

from openedx.core.djangolib.testing.utils import skip_unless_cms
from openedx.features.edly.tests.factories import (
  EdlyOrganizationFactory,
  EdlySubOrganizationFactory,
  SiteFactory,
)
from student.tests.factories import UserFactory

LOGGER_NAME = 'openedx.features.edly.utils'


@skip_unless_cms
@patch.dict('django.conf.settings.FEATURES', {'ORGANIZATIONS_APP': True})
@override_switch(settings.ENABLE_EDLY_ORGANIZATIONS_SWITCH, active=True)
class TestEdlyOrganizationListing(TestCase):
    """
    Verify Organization listing behavior.
    """
    @patch.dict('django.conf.settings.FEATURES', {'ORGANIZATIONS_APP': True})
    def setUp(self):
        super(TestEdlyOrganizationListing, self).setUp()
        self.staff = UserFactory(is_staff=True)
        self.client.login(username=self.staff.username, password='test')
        self.org_names_listing_url = reverse('organizations')

    def test_without_authentication(self):
        """
        Verify authentication is required when accessing the endpoint.
        """
        self.client.logout()
        response = self.client.get(self.org_names_listing_url)
        assert response.status_code == 302

    def test_organization_list(self):
        """
        Verify that the organization names list API only returns Edly's enabled organizations.
        """
        studio_site = SiteFactory()
        edly_organization = EdlyOrganizationFactory(name='Test Edly Organization Name')
        edly_sub_organization = EdlySubOrganizationFactory(
            studio_site=studio_site,
            edly_organization=edly_organization
        )

        response = self.client.get(self.org_names_listing_url, HTTP_ACCEPT='application/json', SERVER_NAME=studio_site.domain)

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0] == edly_sub_organization.edx_organization.short_name

    def test_organization_list_without_linked_edly_sub_organization(self):
        """
        Verify that organization list API returns empty response without enabled organizations.

        The organization names list API returns empty response when there is no
        linked "EdlySubOrganization" with the studio site.
        """
        studio_site = SiteFactory()
        with LogCapture(LOGGER_NAME) as logger:
            response = self.client.get(self.org_names_listing_url, HTTP_ACCEPT='application/json', SERVER_NAME=studio_site.domain)

            logger.check(
                (
                    LOGGER_NAME,
                    'ERROR',
                    'No EdlySubOrganization found for site {}'.format(studio_site)
                )
            )

            assert response.status_code == 200
            assert response.json() == []
