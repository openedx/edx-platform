"""
Tests for Edly Utils Functions.
"""
import jwt
import mock
from mock import MagicMock

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory

from openedx.core.djangoapps.user_authn.cookies import standard_cookie_settings as cookie_settings
from openedx.core.djangolib.testing.utils import skip_unless_cms
from openedx.features.edly import cookies as cookies_api
from openedx.features.edly.tests.factories import EdlySubOrganizationFactory, EdlyUserProfileFactory, SiteFactory
from openedx.features.edly.utils import (
    create_user_link_with_edly_sub_organization,
    decode_edly_user_info_cookie,
    encode_edly_user_info_cookie,
    get_edly_sub_org_from_cookie,
    get_edx_org_from_cookie,
    set_global_course_creator_status,
    update_course_creator_status,
    user_has_edly_organization_access,
    user_belongs_to_edly_organization,
)
from student import auth
from student.roles import (
    CourseCreatorRole,
    GlobalCourseCreatorRole,
)
from student.tests.factories import UserFactory

def mock_render_to_string(template_name, context):
    """
    Return a string that encodes template_name and context
    """
    return str((template_name, context))

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
        self.admin_user = UserFactory.create(is_staff=True)
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

    def _get_course_creator_status(self, user):
        """
        Helper method to get user's course creator status.
        """
        from course_creators.views import get_course_creator_status

        return get_course_creator_status(user)

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
        response = cookies_api.set_logged_in_edly_cookies(
            self.request, HttpResponse(),
            self.user,
            cookie_settings(self.request)
        )
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

    def test_user_linked_with_edly_organization(self):
        """
        Test user is linked with a valid site.
        """
        edly_sub_organization = EdlySubOrganizationFactory(lms_site=self.request.site)
        self.edly_user_profile.edly_sub_organizations.add(edly_sub_organization)

        assert user_belongs_to_edly_organization(self.request, self.user) is True

    def test_user_not_linked_with_edly_organization(self):
        """
        Test user is not linked with a valid site.
        """
        self._create_edly_sub_organization()

        assert user_belongs_to_edly_organization(self.request, self.user) is False

    def test_get_edly_sub_org_from_cookie(self):
        """
        Test that "get_edly_sub_org_from_cookie" method returns edly-sub-org slug correctly.
        """
        edly_sub_organization = self._create_edly_sub_organization()
        edly_user_info_cookie = cookies_api._get_edly_user_info_cookie_string(self.request)
        assert edly_sub_organization.slug == get_edly_sub_org_from_cookie(edly_user_info_cookie)

    def test_get_edx_org_from_cookie(self):
        """
        Test that "get_edx_org_from_cookie" method returns edx-org short name correctly.
        """
        edly_sub_organization = self._create_edly_sub_organization()
        edly_user_info_cookie = cookies_api._get_edly_user_info_cookie_string(self.request)
        assert edly_sub_organization.edx_organization.short_name == get_edx_org_from_cookie(edly_user_info_cookie)

    def test_create_user_link_with_edly_sub_organization(self):
        """
        Test that "create_user_link_with_edly_sub_organization" method create "EdlyUserProfile" link with User.
        """
        user = UserFactory()
        edly_sub_organization = self._create_edly_sub_organization()
        edly_user_profile = create_user_link_with_edly_sub_organization(self.request, user)
        assert edly_user_profile == user.edly_profile
        assert edly_sub_organization.slug in user.edly_profile.get_linked_edly_sub_organizations

    @skip_unless_cms
    @mock.patch('course_creators.admin.render_to_string', mock.Mock(side_effect=mock_render_to_string, autospec=True))
    def test_update_course_creator_status(self):
        """
        Test that "update_course_creator_status" method sets/removes a User as Course Creator correctly.
        """
        settings.FEATURES['ENABLE_CREATOR_GROUP'] = True
        update_course_creator_status(self.admin_user, self.user, True)
        assert self._get_course_creator_status(self.user) == 'granted'
        assert auth.user_has_role(self.user, CourseCreatorRole())

        update_course_creator_status(self.admin_user, self.user, False)
        assert self._get_course_creator_status(self.user) == 'unrequested'
        assert not auth.user_has_role(self.user, CourseCreatorRole())

        self.admin_user.is_staff = False
        self.admin_user.save()
        with self.assertRaises(PermissionDenied):
            update_course_creator_status(self.admin_user, self.user, True)

        edly_panel_admin_user_group, __ = Group.objects.get_or_create(name=settings.EDLY_PANEL_ADMIN_USERS_GROUP)
        self.admin_user.groups.add(edly_panel_admin_user_group)
        update_course_creator_status(self.admin_user, self.user, False)
        assert self._get_course_creator_status(self.user) == 'unrequested'
        assert not auth.user_has_role(self.user, CourseCreatorRole())

    @skip_unless_cms
    @mock.patch('course_creators.admin.render_to_string', mock.Mock(side_effect=mock_render_to_string, autospec=True))
    def test_set_global_course_creator_status(self):
        """
        Test that "set_global_course_creator_status" method sets/removes a User as Global Course Creator correctly.
        """
        self._create_edly_sub_organization()
        response = cookies_api.set_logged_in_edly_cookies(self.request, HttpResponse(), self.user, cookie_settings(self.request))
        self._copy_cookies_to_request(response, self.request)
        edly_user_info_cookie = self.request.COOKIES.get(settings.EDLY_USER_INFO_COOKIE_NAME)
        edx_org = get_edx_org_from_cookie(edly_user_info_cookie)
        self.request.user = self.admin_user

        set_global_course_creator_status(self.request, self.user, True)
        assert self._get_course_creator_status(self.user) == 'granted'
        assert auth.user_has_role(self.user, GlobalCourseCreatorRole(edx_org))

        set_global_course_creator_status(self.request, self.user, False)
        assert self._get_course_creator_status(self.user) == 'unrequested'
        assert not auth.user_has_role(self.user, GlobalCourseCreatorRole(edx_org))

        self.admin_user.is_staff = False
        self.admin_user.save()
        with self.assertRaises(PermissionDenied):
            set_global_course_creator_status(self.request, self.user, True)

        edly_panel_admin_user_group, __ = Group.objects.get_or_create(name=settings.EDLY_PANEL_ADMIN_USERS_GROUP)
        self.admin_user.groups.add(edly_panel_admin_user_group)
        set_global_course_creator_status(self.request, self.user, True)
        assert self._get_course_creator_status(self.user) == 'granted'
        assert auth.user_has_role(self.user, CourseCreatorRole())
