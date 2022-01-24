"""
Unit tests for Permissions.
"""
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.edly.permissions import CanAccessEdxAPI
from openedx.features.edly.tests.factories import (
    EdlySubOrganizationFactory,
    EdlyUserFactory,
    EdlyUserProfileFactory,
)


class CanAccessEdxAPITests(TestCase):
    """
    Test `CanAccessEdxAPI` permission class.
    """

    def setUp(self):
        super(CanAccessEdxAPITests, self).setUp()
        self.user = EdlyUserFactory()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.site = SiteFactory()

    def test_user_can_access_api_on_linked_site(self):
        """
        Verify that user can access API on the site that is linked with edly profile.
        """
        edly_sub_organization = EdlySubOrganizationFactory(lms_site=self.request.site)
        edly_user_profile = EdlyUserProfileFactory(user=self.user)
        edly_user_profile.edly_sub_organizations.add(edly_sub_organization)  # pylint: disable=E1101
        permission = CanAccessEdxAPI().has_permission(self.request, None)
        assert permission

    def test_user_cannot_access_api_on_non_linked_site(self):
        """
        Verify that user can not access API on the site that is not linked with its edly profile.
        """
        EdlySubOrganizationFactory(lms_site=self.request.site)
        permission = CanAccessEdxAPI().has_permission(self.request, None)
        assert not permission

    def test_staff_can_access_api(self):
        """
        Verify that staff can access API.
        """
        self.request.user.is_staff = True
        permission = CanAccessEdxAPI().has_permission(self.request, None)
        assert permission
