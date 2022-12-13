"""
Tests for Edly User Registration.
"""
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.features.edly.tests.factories import EdlySubOrganizationFactory



class EdlyUserRegistrationTests(TestCase):
    """
    Tests for Edly User Registration.
    """

    def setUp(self):
        """
        Setup initial test data
        """
        super(EdlyUserRegistrationTests, self).setUp()
        self.url = reverse('user_api_registration')
        self.site_config = SiteConfigurationFactory()
        self.site = self.site_config.site

    def test_edly_profile_creation_with_user_registration(self):
        """
        Test "EdlyUserProfile" creation on Registration of User.

        Create an account with params, assert that the response indicates
        success, and check if "EdlyUserProfile" object exists for the newly created user
        """

        EdlySubOrganizationFactory(lms_site=self.site)
        username = 'test_user'
        params = {
            'email': 'test@example.org',
            'name': 'Test User',
            'username': username,
            'password': 'test-pass',
            'honor_code': 'true',
        }

        response = self.client.post(self.url, params, SERVER_NAME=self.site.domain)
        assert response.status_code == 200

        edly_user = User.objects.get(username=username)
        assert hasattr(edly_user, 'edly_profile') == True
        assert self.site.edly_sub_org_for_lms.slug in edly_user.edly_profile.get_linked_edly_sub_organizations
