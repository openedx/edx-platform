"""
Tests for Edly API ViewSets.
"""
import json

from django.test import TestCase, RequestFactory, Client
from django.urls import reverse

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from openedx.features.edly.tests.factories import EdlySubOrganizationFactory
from student.tests.factories import UserFactory


@skip_unless_lms
class TestUserSitesViewSet(TestCase):
    """
    Tests for "UserSitesViewSet".
    """

    def setUp(self):
        """
        Setup initial test data
        """
        super(TestUserSitesViewSet, self).setUp()
        self.request_site = SiteFactory()
        self.edly_sub_org = EdlySubOrganizationFactory(lms_site=self.request_site, studio_site=self.request_site, preview_site=self.request_site)
        self.request = RequestFactory(SERVER_NAME=self.request_site.domain).get('')
        self.request.site = self.request_site
        self.user = UserFactory(is_staff=True, is_superuser=True, edly_multisite_user__sub_org=self.edly_sub_org)
        self.request.user = self.user
        self.client = Client(SERVER_NAME=self.request_site.domain)
        self.client.login(username=self.user.username, password='test')
        self.user_sites_list_url = reverse('user_sites-list')

    def test_list_with_logged_in_user(self):
        """
        Verify that `list` returns correct response when user is logged in.
        """
        response = self.client.get(self.user_sites_list_url)

        assert response.status_code == 200

        data = response.data[0]
        assert data.get('site_data', {}).get('display_name') == self.request_site.name
        assert not data.get('app_config')

    def test_list_without_logged_in_user(self):
        """
        Verify that `list` returns correct response when user is not logged in.
        """
        self.client.logout()
        response = self.client.get(self.user_sites_list_url)
        assert response.status_code == 401
