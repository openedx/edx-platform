"""
Tests for the tiers integration in Studio.
"""

from django.urls import reverse
from django.test import TestCase, override_settings
from rest_framework import status

from openedx.core.djangoapps.appsembler.multi_tenant_emails.tests.test_utils import (
    with_organization_context,
    create_org_user,
)


class SiteUnavailableStudioViewTest(TestCase):
    """
    Unit tests for the Tiers views.
    """

    BLUE = 'blue2'
    PASSWORD = 'xyz'

    def setUp(self):
        super(SiteUnavailableStudioViewTest, self).setUp()
        self.url = reverse('site_unavailable')

        with override_settings(DEFAULT_SITE_THEME='edx-theme-codebase'):
            with with_organization_context(self.BLUE) as org:
                self.admin = create_org_user(org, password=self.PASSWORD)

    def test_site_unavailable_page_non_logged_in(self):
        """
        The trial page needs a logged in user because Studio isn't multi-site aware.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_302_FOUND, response.content
        assert response['Location'] == '/signin?next=/site-unavailable/', response.content

    def test_site_unavailable_page(self):
        """
        Ensure trial expire page shows up with site information.
        """
        assert self.client.login(username=self.admin.username, password=self.PASSWORD), 'Admin should log in'
        response = self.client.get(self.url)
        message = 'The trial site of {} has expired.'.format(self.BLUE)
        assert message in response.content, 'Trial page works.'
