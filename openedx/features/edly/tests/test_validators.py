"""
Unit tests for Validators.
"""
from django.test import TestCase
from django.test.client import RequestFactory
from student.tests.factories import UserFactory

from openedx.features.edly.tests.factories import (
    EdlySubOrganizationFactory,
    SiteFactory
)
from openedx.features.edly.validators import (
    is_edly_user_allowed_to_login,
    is_edly_user_allowed_to_login_with_social_auth
)


class EdlyValidatorsTests(TestCase):

    def setUp(self):
        self.request = RequestFactory().get('/login')
        self.request.site = SiteFactory()
        self.edly_sub_organization = EdlySubOrganizationFactory(lms_site=self.request.site)
        self.user = UserFactory.create(edly_multisite_user__sub_org=self.edly_sub_organization)

    def test_user_with_edly_sub_organization_access_of_current_site(self):
        """
        Test user has access to current site as it's edly sub organization
        is linked with user's "EdlyUserProfile".
        """
        has_access = is_edly_user_allowed_to_login(self.request, self.user)

        assert has_access

    def test_user_without_edly_sub_organization_access_for_current_site(self):
        """
        Test user has no access to current site as it's edly sub organization
        is not linked with user's "EdlyUserProfile".
        """
        user = UserFactory()
        has_access = is_edly_user_allowed_to_login(self.request, user)

        assert not has_access

    def test_user_allow_to_login_with_social_auth(self):
        """
        Test user can login to site with social auth.
        """
        has_access = is_edly_user_allowed_to_login_with_social_auth(self.request, self.user)

        assert has_access

    def test_user_allow_to_login_with_social_auth(self):
        """
        Test user can not login to site with social auth.
        """
        user = UserFactory()
        has_access = is_edly_user_allowed_to_login_with_social_auth(self.request, user)

        assert not has_access
