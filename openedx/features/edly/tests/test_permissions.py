"""
Unit tests for Permissions.
"""
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from openedx.features.edly.permissions import CanAccessEdxAPI
from openedx.features.edly.tests.factories import (
    EdlySubOrganizationFactory,
)
from student.tests.factories import UserFactory


class CanAccessEdxAPITests(TestCase):
    """
    Test `CanAccessEdxAPI` permission class.
    """

    def setUp(self):
        super(CanAccessEdxAPITests, self).setUp()
        self.request = RequestFactory().get('/')
        self.request.site = SiteFactory()

    def test_user_can_access_api_on_linked_site(self):
        """
        Verify that user can access API on the site that is linked with edly profile.
        """
        edly_sub_organization = EdlySubOrganizationFactory(lms_site=self.request.site)
        edly_user_profile = UserFactory(edly_multisite_user__sub_org=edly_sub_organization)
        self.request.user = edly_user_profile
        permission = CanAccessEdxAPI().has_permission(self.request, None)
        assert permission

    def test_user_cannot_access_api_on_non_linked_site(self):
        """
        Verify that user can not access API on the site that is not linked with its edly profile.
        """
        EdlySubOrganizationFactory(lms_site=self.request.site)
        user = UserFactory()
        self.request.user = user
        permission = CanAccessEdxAPI().has_permission(self.request, None)
        assert not permission

    def test_staff_can_access_api(self):
        """
        Verify that staff can access API.
        """
        edly_sub_organization = EdlySubOrganizationFactory(lms_site=self.request.site)
        edly_user_profile = UserFactory(edly_multisite_user__sub_org=edly_sub_organization)
        self.request.user = edly_user_profile
        self.request.user.is_staff = True
        permission = CanAccessEdxAPI().has_permission(self.request, None)
        assert permission
