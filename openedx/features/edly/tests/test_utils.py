"""
Tests for Edly Utils Functions.
"""
import jwt
from mock import MagicMock

from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.features.edly import cookies as cookies_api
from openedx.features.edly.tests.factories import EdlySubOrganizationFactory, EdlyUserProfileFactory, SiteFactory
from openedx.features.edly.utils import (
    create_user_link_with_edly_sub_organization,
    decode_edly_user_info_cookie,
    encode_edly_user_info_cookie,
    get_edly_sub_org_from_cookie,
    user_has_edly_organization_access
)
from student.tests.factories import UserFactory


class UtilsTests(TestCase):
    """
    Tests for utility methods.
    """

    def setUp(self):
        """
        Setup initial test data
        """
        super(UtilsTests, self).setUp()
        self.user = UserFactory.create()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = self._get_stub_session()
        self.request.site = SiteFactory()

        self.edly_user_profile = EdlyUserProfileFactory(user=self.user)
        self.test_edly_user_info_cookie_data = {
            'edly-org': 'edly',
            'edly-sub-org': 'cloud',
            'edx-org': 'cloudX'
        }

    def _get_stub_session(self, expire_at_browser_close=False, max_age=604800):
        return MagicMock(
            get_expire_at_browser_close=lambda: expire_at_browser_close,
            get_expiry_age=lambda: max_age,
        )

    def _copy_cookies_to_request(self, response, request):
        request.COOKIES = {
            key: val.value
            for key, val in response.cookies.iteritems()
        }

    def _create_edly_sub_organization(self):
        """
        Helper method to create 'EdlySubOrganization` for the request site.
        """
        return EdlySubOrganizationFactory(lms_site=self.request.site)

    def test_encode_edly_user_info_cookie(self):
        """
        Test that "encode_edly_user_info_cookie" method encodes data correctly.
        """
        actual_encoded_string = encode_edly_user_info_cookie(self.test_edly_user_info_cookie_data)
        expected_encoded_string = jwt.encode(
            self.test_edly_user_info_cookie_data, settings.EDLY_COOKIE_SECRET_KEY,
            algorithm=settings.EDLY_JWT_ALGORITHM
        )
        assert actual_encoded_string == expected_encoded_string

    def test_decode_edly_user_info_cookie(self):
        """
        Test that "decode_edly_user_info_cookie" method decodes data correctly.
        """
        encoded_data = jwt.encode(
            self.test_edly_user_info_cookie_data,
            settings.EDLY_COOKIE_SECRET_KEY,
            algorithm=settings.EDLY_JWT_ALGORITHM
        )
        decoded_edly_user_info_cookie_data = decode_edly_user_info_cookie(encoded_data)
        assert self.test_edly_user_info_cookie_data == decoded_edly_user_info_cookie_data

    def test_user_with_organization_access(self):
        """
        Test user have access to a valid site URL which is linked to that user.
        """
        self._create_edly_sub_organization()
        response = cookies_api.set_logged_in_edly_cookies(self.request, HttpResponse(), self.user)
        self._copy_cookies_to_request(response, self.request)

        user_has_access = user_has_edly_organization_access(self.request)
        assert user_has_access is True

    def test_user_without_organization_access(self):
        """
        Test user has no access to a valid site URL but that site in not linked to the user.
        """
        edly_sub_organization = EdlySubOrganizationFactory(lms_site=SiteFactory())
        self.edly_user_profile.edly_sub_organizations.add(edly_sub_organization)

        user_has_access = user_has_edly_organization_access(self.request)
        assert user_has_access is False

    def test_get_edly_sub_org_from_cookie(self):
        """
        Test that "get_edly_sub_org_from_cookie" method returns edly-sub-org slug correctly.
        """
        edly_sub_organization = self._create_edly_sub_organization()
        edly_user_info_cookie = cookies_api._get_edly_user_info_cookie_string(self.request)
        assert edly_sub_organization.slug == get_edly_sub_org_from_cookie(edly_user_info_cookie)

    def test_create_user_link_with_edly_sub_organization(self):
        """
        Test that "create_user_link_with_edly_sub_organization" method create "EdlyUserProfile" link with User.
        """
        user = UserFactory()
        edly_sub_organization = self._create_edly_sub_organization()
        edly_user_profile = create_user_link_with_edly_sub_organization(self.request, user)
        assert edly_user_profile == user.edly_profile
        assert edly_sub_organization.slug in user.edly_profile.get_linked_edly_sub_organizations
