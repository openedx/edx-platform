import jwt
from mock import MagicMock, patch

from django.conf import settings
from django.http import HttpResponse
from django.test import RequestFactory, TestCase

from openedx.core.djangoapps.user_authn.cookies import standard_cookie_settings as cookie_settings
from openedx.features.edly.tests.factories import SiteFactory, EdlySubOrganizationFactory
from openedx.features.edly import cookies as cookies_api
from student import auth
from student.roles import CourseCreatorRole
from student.tests.factories import UserFactory, GroupFactory


class CookieTests(TestCase):
    """
    Test cases for Edly cookie methods.
    """

    def setUp(self):
        """
        Setup initial test data
        """
        super(CookieTests, self).setUp()
        self.user = UserFactory.create()
        edly_panel_users_group = GroupFactory(name=settings.EDLY_PANEL_USERS_GROUP)
        self.user.groups.add(edly_panel_users_group)
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.session = self._get_stub_session()
        self.request.site = SiteFactory()
        self.cookie_settings = cookie_settings(self.request)

    def _get_stub_session(self, expire_at_browser_close=False, max_age=604800):
        return MagicMock(
            get_expire_at_browser_close=lambda: expire_at_browser_close,
            get_expiry_age=lambda: max_age,
        )

    def _create_edly_sub_organization(self):
        """
        Helper method to create 'EdlySubOrganization` for the request site.
        """
        return EdlySubOrganizationFactory(lms_site=self.request.site)

    def test_get_edly_cookie_string(self):
        """
        Tests that edly cookie string is generated correctly.
        """
        edly_sub_organization = self._create_edly_sub_organization()
        actual_cookie_string = cookies_api._get_edly_user_info_cookie_string(self.request)  # pylint: disable=protected-access
        expected_cookie_string = jwt.encode(
            {
                'edly-org': edly_sub_organization.edly_organization.slug,
                'edly-sub-org': edly_sub_organization.slug,
                'edx-orgs': edly_sub_organization.get_edx_organizations,
                'is_course_creator': auth.user_has_role(self.request.user, CourseCreatorRole()),
                'user_groups': list(self.user.groups.all().values_list('name', flat=True))
            },
            settings.EDLY_COOKIE_SECRET_KEY,
            algorithm=settings.EDLY_JWT_ALGORITHM
        )
        assert actual_cookie_string == expected_cookie_string.decode('utf-8')

    def test_set_logged_in_edly_cookies(self):
        """
        Tests that Edly user info cookie is set correctly.
        """
        self._create_edly_sub_organization()
        response = cookies_api.set_logged_in_edly_cookies(self.request, HttpResponse(), self.user, self.cookie_settings)
        assert settings.EDLY_USER_INFO_COOKIE_NAME in response.cookies

    def test_set_logged_in_edly_cookies_with_no_edly_sub_organiztion(self):
        """
        Tests that Edly user info cookie is set to empty in absence of edly sub-organization.
        """
        response = cookies_api.set_logged_in_edly_cookies(self.request, HttpResponse(), self.user, self.cookie_settings)
        assert settings.EDLY_USER_INFO_COOKIE_NAME in response.cookies
        assert response.cookies.get(settings.EDLY_USER_INFO_COOKIE_NAME).value == ''

    def test_delete_logged_in_edly_cookies(self):
        """
        Tests that Edly user info cookie is deleted correctly.
        """
        self._create_edly_sub_organization()
        response = cookies_api.set_logged_in_edly_cookies(self.request, HttpResponse(), self.user, self.cookie_settings)
        assert settings.EDLY_USER_INFO_COOKIE_NAME in response.cookies

        cookies_api.delete_logged_in_edly_cookies(response)
        assert not response.cookies.get(settings.EDLY_USER_INFO_COOKIE_NAME).value
