"""
Tests for Edly Utils Functions.
"""
from urllib.parse import urljoin
import jwt
import mock
from mock import MagicMock

import crum
import ddt
from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.test import modify_settings
from django.test.client import RequestFactory
from edx_django_utils.cache import RequestCache
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.core.djangoapps.user_authn.cookies import standard_cookie_settings as cookie_settings
from openedx.core.djangolib.testing.utils import skip_unless_cms
from openedx.features.edly import cookies as cookies_api
from openedx.features.edly.tests.factories import (
    EdlyOrganizationFactory,
    EdlySubOrganizationFactory,
    EdlyUserProfileFactory,
    SiteFactory,
)
from openedx.features.edly.utils import (
    create_user_link_with_edly_sub_organization,
    create_learner_link_with_permission_groups,
    decode_edly_user_info_cookie,
    edly_panel_user_has_edly_org_access,
    encode_edly_user_info_cookie,
    get_edly_sub_org_from_cookie,
    get_edx_org_from_cookie,
    get_marketing_link,
    is_course_org_same_as_site_org,
    set_global_course_creator_status,
    update_course_creator_status,
    user_has_edly_organization_access,
    user_belongs_to_edly_sub_organization,
    user_can_login_on_requested_edly_organization,
    filter_courses_based_on_org,
    get_current_site_invalid_certificate_context,
)
from organizations.tests.factories import OrganizationFactory
from student import auth
from student.roles import (
    CourseCreatorRole,
    GlobalCourseCreatorRole,
)
from student.tests.factories import UserFactory, GroupFactory
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


def mock_render_to_string(template_name, context):
    """
    Return a string that encodes template_name and context
    """
    return str((template_name, context))


@modify_settings(
    MIDDLEWARE={
        'append': [
            'openedx.features.edly.middleware.EdlyOrganizationAccessMiddleware',
            'openedx.features.edly.middleware.SettingsOverrideMiddleware',
        ]
    }
)
@ddt.ddt
class UtilsTests(SharedModuleStoreTestCase):
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
        self.course = CourseOverviewFactory()
        RequestCache.clear_all_namespaces()

    def _get_stub_session(self, expire_at_browser_close=False, max_age=604800):
        return MagicMock(
            get_expire_at_browser_close=lambda: expire_at_browser_close,
            get_expiry_age=lambda: max_age,
        )

    def _copy_cookies_to_request(self, response, request):
        request.COOKIES = {
            key: val.value
            for key, val in response.cookies.items()
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
        assert actual_encoded_string == expected_encoded_string.decode('utf-8')

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

    def test_staff_user_with_organization_access(self):
        """
        Test staff user have access to a valid site URL which is not linked to that user.
        """
        self.request.user = self.admin_user
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

    def test_user_linked_with_edly_sub_organization(self):
        """
        Test user is linked with a valid site.
        """
        edly_sub_organization = EdlySubOrganizationFactory(lms_site=self.request.site)
        self.edly_user_profile.edly_sub_organizations.add(edly_sub_organization)

        assert user_belongs_to_edly_sub_organization(self.request, self.user) is True

    def test_user_not_linked_with_edly_sub_organization(self):
        """
        Test user is not linked with a valid site.
        """
        self._create_edly_sub_organization()

        assert user_belongs_to_edly_sub_organization(self.request, self.user) is False

    def test_user_can_login_on_requested_edly_organization(self):
        """
        Test user can login on the requested URL site if linked with its parent edly-organization.
        """
        edly_sub_organization_linked_to_site = self._create_edly_sub_organization()
        edly_sub_organization_linked_to_user = EdlySubOrganizationFactory(
            lms_site=SiteFactory(),
            edly_organization=edly_sub_organization_linked_to_site.edly_organization,
        )
        self.edly_user_profile.edly_sub_organizations.add(edly_sub_organization_linked_to_user)

        assert user_can_login_on_requested_edly_organization(self.request, self.user) is False

        edly_sub_organization_linked_to_site.edly_organization.enable_all_edly_sub_org_login = True
        edly_sub_organization_linked_to_site.edly_organization.save()

        assert user_can_login_on_requested_edly_organization(self.request, self.user) is True

    def test_user_cannot_login_on_requested_edly_organization(self):
        """
        Test user cannot login on the requested URL site if not linked with its parent edly-organization.
        """
        assert user_can_login_on_requested_edly_organization(self.request, self.user) is False

        edly_sub_organization_linked_to_site = self._create_edly_sub_organization()

        edly_sub_organization_linked_to_user = EdlySubOrganizationFactory(
            lms_site=SiteFactory(),
            edly_organization=EdlyOrganizationFactory(),
        )
        self.edly_user_profile.edly_sub_organizations.add(edly_sub_organization_linked_to_user)

        assert user_can_login_on_requested_edly_organization(self.request, self.user) is False

        edly_sub_organization_linked_to_site.edly_organization.enable_all_edly_sub_org_login = True
        edly_sub_organization_linked_to_site.edly_organization.save()

        assert user_can_login_on_requested_edly_organization(self.request, self.user) is False

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
        assert edly_sub_organization.get_edx_organizations == get_edx_org_from_cookie(edly_user_info_cookie)

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

    def test_edly_panel_user_has_edly_org_access(self):
        """
        Test if a user is edly panel user or edly panel admin user.
        """
        self._create_edly_sub_organization()
        create_user_link_with_edly_sub_organization(self.request, self.request.user)

        assert not edly_panel_user_has_edly_org_access(self.request)

        edly_panel_user_group = GroupFactory(name=settings.EDLY_PANEL_USERS_GROUP)
        self.request.user.groups.add(edly_panel_user_group)
        assert edly_panel_user_has_edly_org_access(self.request)

    def test_filter_courses_based_on_org(self):
        """
        Test course are filtered properly on current site organization.
        """
        edx_org_1 = OrganizationFactory()
        edx_org_2 = OrganizationFactory()
        courses_of_org_1 = CourseFactory.create_batch(2, org=edx_org_1.short_name)
        CourseFactory.create(org=edx_org_2.short_name)

        assert len(modulestore().get_courses()) == 3

        EdlySubOrganizationFactory(
            edx_organizations=[edx_org_1],
            lms_site=self.request.site,
            studio_site=self.request.site
        )
        create_user_link_with_edly_sub_organization(self.request, self.request.user)
        response = cookies_api.set_logged_in_edly_cookies(
            self.request, HttpResponse(),
            self.user,
            cookie_settings(self.request)
        )
        self._copy_cookies_to_request(response, self.request)

        filtered_courses = filter_courses_based_on_org(self.request, courses_of_org_1)
        assert len(filtered_courses) == 2

        edx_orgs_of_filterd_courses = [course.org for course in filtered_courses]
        for org in edx_orgs_of_filterd_courses:
            assert org == edx_org_1.short_name

    def test_create_learner_link_with_permission_groups(self):
        """
        Test that "create_learner_link_with_permission_groups" method create learner groups permissions.
        """
        edly_user = UserFactory()
        edly_user_group = GroupFactory(name=settings.EDLY_USER_ROLES.get('subscriber', None))

        edly_user = create_learner_link_with_permission_groups(edly_user)
        assert edly_user.groups.filter(name=edly_user_group).exists()

    def test_get_current_site_invalid_certificate_context_without_site_configuration(self):
        """
        Test method returns correct data without site configuration.
        """
        crum.set_current_request(request=RequestFactory().get('/'))
        test_default_certificate_html_configurations = {
            'default': {
                'accomplishment_class_append': 'accomplishment-certificate',
                'platform_name': 'fake-platform-name',
                'logo_src': 'fake-logo-path',
                'logo_url': 'fake-logo-url',
                'company_verified_certificate_url': 'fake-verified-certificate-url',
                'company_privacy_url': 'fake-privacy-url',
                'company_tos_url': 'fake-tos-url',
                'company_about_url': 'fake-about-url'
            }
        }

        expected_current_site_context_data = test_default_certificate_html_configurations['default']
        curent_site_context_data = get_current_site_invalid_certificate_context(test_default_certificate_html_configurations)

        assert expected_current_site_context_data['platform_name'] == curent_site_context_data['platform_name']
        assert expected_current_site_context_data['company_privacy_url'] == curent_site_context_data['company_privacy_url']
        assert expected_current_site_context_data['company_tos_url'] == curent_site_context_data['company_tos_url']

    @mock.patch('openedx.core.djangoapps.theming.helpers.get_current_site')
    def test_get_current_site_invalid_certificate_context_with_site_configuration(self, mocked_get_current_site):
        """
        Test method returns correct data with site configuration.
        """
        test_default_certificate_html_configurations = {
            'default': {
                'accomplishment_class_append': 'accomplishment-certificate',
                'platform_name': 'fake-platform-name',
                'logo_src': 'fake-logo-path',
                'logo_url': 'fake-logo-url',
                'company_verified_certificate_url': 'fake-verified-certificate-url',
                'company_privacy_url': 'fake-privacy-url',
                'company_tos_url': 'fake-tos-url',
                'company_about_url': 'fake-about-url'
            }
        }

        SiteConfigurationFactory(
            site=self.request.site,
            site_values={
                'ENABLE_MKTG_SITE': True,
                'platform_name': 'fake-2nd-platform-name',
                'MKTG_URLS': {
                    'ROOT': 'http://{}'.format(self.request.site.domain),
                    'PRIVACY': '/fake-privacy-path',
                    'TOS_AND_HONOR': '/fake-tos-path',
                }
            }
        )
        crum.set_current_request(request=self.request)
        mocked_get_current_site.return_value = self.request.site
        current_site_context_data = get_current_site_invalid_certificate_context(test_default_certificate_html_configurations)

        expected_current_site_context = test_default_certificate_html_configurations['default']
        expected_current_site_context['platform_name'] = self.request.site.configuration.site_values.get(
            'platform_name'
        )
        assert expected_current_site_context['platform_name'] == current_site_context_data['platform_name']

        marketing_urls = self.request.site.configuration.get_value('MKTG_URLS', {})
        marketing_root_url = marketing_urls.get('ROOT')

        tos_path = marketing_urls.get('TOS_AND_HONOR')
        expected_company_tos_url = '{}{}'.format(marketing_root_url, tos_path)
        assert expected_company_tos_url == current_site_context_data['company_tos_url']

        privacy_path = marketing_urls.get('PRIVACY')
        expected_company_privacy_url = '{}{}'.format(marketing_root_url, privacy_path)
        assert expected_company_privacy_url == current_site_context_data['company_privacy_url']

    def test_clean_django_settings_override_for_disallowed_settings(self):
        """
        Test disallowed settings raise correct validation error.
        """
        default_settings = {
            key: getattr(settings, key, None) for key in settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE
        }
        dissallowed_test_settings = dict(default_settings, HELLO='world')
        expected_error_message = 'Django settings override(s) "HELLO" is/are not allowed to be overridden.'

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            site_configuration = SiteConfigurationFactory(
                site=SiteFactory(),
                site_values={
                    'DJANGO_SETTINGS_OVERRIDE': dissallowed_test_settings
                }
            )
            site_configuration.clean()

    def test_clean_django_settings_override_for_missing_settings(self):
        """
        Test missing settings raise correct validation error.
        """
        default_settings = {
            key: getattr(settings, key, None) for key in settings.ALLOWED_DJANGO_SETTINGS_OVERRIDE
        }
        missing_test_settings = default_settings.copy()
        missing_test_settings.pop('LMS_BASE')
        expected_error_message = 'Django settings override(s) "LMS_BASE" is/are missing.'

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            site_configuration = SiteConfigurationFactory(
                site=SiteFactory(),
                site_values={
                    'DJANGO_SETTINGS_OVERRIDE': missing_test_settings
                }
            )
            site_configuration.clean()

    def test_get_marketing_link_with_value(self):
        """
        Test marketing link value with name in marketing urls
        """
        marketing_urls = {
            'ROOT': 'http://{}'.format(self.request.site.domain),
            'PRIVACY': '/fake-privacy-path',
            'TOS': '/fake-tos-path',
        }
        expected_privacy_marketing_link = urljoin(marketing_urls.get('ROOT'), marketing_urls.get('PRIVACY'))
        privacy_marketing_link = get_marketing_link(marketing_urls, 'PRIVACY')
        assert expected_privacy_marketing_link == privacy_marketing_link

        expected_tos_marketing_link = urljoin(marketing_urls.get('ROOT'), marketing_urls.get('TOS'))
        tos_marketing_link = get_marketing_link(marketing_urls, 'TOS')
        assert expected_tos_marketing_link == tos_marketing_link

    def test_get_marketing_link_without_value(self):
        """
        Test marketing link value without name in marketing urls
        """
        marketing_urls = {
            'ROOT': 'http://{}'.format(self.request.site.domain),
        }
        expected_marketing_link = ''
        marketing_link = get_marketing_link(marketing_urls, 'HONOR')
        assert expected_marketing_link == marketing_link

    @ddt.data(
        ('edX', 'course-v1:edX+Test+Test_Course', True),
        ('edly', 'course-v1:edX+Test+Test_Course', False),
    )
    @ddt.unpack
    def test_is_course_org_same_as_site_org(self, edx_org_short_name, course_id, expected_response):
        """
        Test "is_course_org_same_as_site_org" for match & mismatch orgs.
        """
        EdlySubOrganizationFactory(
            edx_organizations=[OrganizationFactory(short_name=edx_org_short_name)],
            lms_site=self.request.site
        )
        course_key = CourseKey.from_string(course_id)
        course = CourseOverviewFactory.create(id=course_key)

        assert expected_response == is_course_org_same_as_site_org(self.request.site, course.id)

    def test_is_course_org_same_as_site_org_for_unlinked_site(self):
        """
        Test "is_course_org_same_as_site_org" when unlinked site is passed.
        """
        assert not is_course_org_same_as_site_org(self.request.site, self.course.id)

    def test_is_course_org_same_as_site_org_for_invalid_course_id(self):
        """
        Test "is_course_org_same_as_site_org" when invalid "course_id" passed.
        """
        EdlySubOrganizationFactory(
            edx_organizations=[OrganizationFactory(short_name='edly')],
            lms_site=self.request.site
        )
        course_id = CourseKey.from_string('course-v1:edX+Test+Test_Course')
        assert not is_course_org_same_as_site_org(self.request.site, course_id)
