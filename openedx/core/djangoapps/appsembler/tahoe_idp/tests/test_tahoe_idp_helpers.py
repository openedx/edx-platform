"""
Tests for `tahoe_idp.helpers`.
"""
from unittest.mock import patch, Mock
from urllib import parse

from django.conf import settings
from django.test import RequestFactory
import pytest

from organizations.tests.factories import OrganizationFactory
from site_config_client.openedx.test_helpers import override_site_config
from tahoe_sites import api as tahoe_sites_apis

from openedx.core.djangoapps.appsembler.tahoe_idp import helpers
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory

from student.roles import (
    CourseAccessRole,
    CourseCreatorRole,
    CourseInstructorRole,
    CourseStaffRole,
    OrgInstructorRole,
    OrgStaffRole,
)

from student.tests.factories import UserFactory


@pytest.fixture
def user_with_org():
    """
    :return: user, organization
    """
    site = SiteFactory.create()
    organization = OrganizationFactory.create()
    tahoe_sites_apis.create_tahoe_site_by_link(organization, site)
    learner = UserFactory.create()
    tahoe_sites_apis.add_user_to_organization(learner, organization, is_admin=False)
    return learner, organization


@pytest.fixture
def valid_request():
    """
    :return: a request that can be used in our tests here
    """
    request = RequestFactory()
    request.GET = {}
    request.is_secure = Mock(return_value=False)
    return request


@pytest.mark.parametrize('global_flags,site_flags,should_be_enabled,message', [
    ({}, {'ENABLE_TAHOE_IDP': True}, True, 'site-flag should enable it'),
    ({'ENABLE_TAHOE_IDP': True}, {}, True, 'cluster-wide flag should enable it'),
    ({}, {}, False, 'When no flag is enabled, the feature should be disabled'),
])
def test_is_tahoe_idp_enabled(settings, global_flags, site_flags, should_be_enabled, message):
    settings.FEATURES = global_flags
    with override_site_config('admin', **site_flags):
        assert helpers.is_tahoe_idp_enabled() == should_be_enabled, message


def test_idp_login_url():
    """
    Tests for `get_idp_login_url`.
    """
    assert helpers.get_idp_login_url() == '/auth/login/tahoe-idp/?auth_entry=login'


def test_idp_login_url_with_next_url():
    """
    Tests for `get_idp_login_url` with next URL.
    """
    url = helpers.get_idp_login_url(next_url='/dashboard?&page=1')
    assert url == '/auth/login/tahoe-idp/?auth_entry=login&next=%2Fdashboard%3F%26page%3D1', 'should encode `next`'


def test_get_idp_register_url():
    url = helpers.get_idp_register_url()
    assert url == '/auth/login/tahoe-idp/?auth_entry=register'


def test_get_idp_register_url_with_next():
    url = helpers.get_idp_register_url(next_url='/courses?per_page=10')
    assert url == '/auth/login/tahoe-idp/?auth_entry=register&next=%2Fcourses%3Fper_page%3D10', 'should add encoded `next`'


def test_get_idp_form_url_with_tahoe_idp_disabled(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}
    with override_site_config('admin', ENABLE_TAHOE_IDP=False):
        assert not helpers.get_idp_form_url(Mock(), Mock(), Mock()), 'Only get a redirect URL when `tahoe-idp` is used'


def test_get_idp_form_url_with_tahoe_tpa_disabled(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': False}
    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(Mock(), Mock(), Mock())

    assert not url, 'Only get a redirect URL when Third Party Auth is used'


def test_get_idp_form_url_for_login(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}
    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(Mock(), 'login', '/home')

    assert url == '/auth/login/tahoe-idp/?auth_entry=login&next=%2Fhome'


@patch('openedx.core.djangoapps.appsembler.tahoe_idp.helpers.pipeline_running', Mock(return_value=False))
def test_get_idp_form_url_for_register_without_pipeline(settings):
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}

    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(None, 'register', '/home')

    assert url == '/auth/login/tahoe-idp/?auth_entry=register&next=%2Fhome', (
        'Return a URL when there is no running pipeline'
    )


@patch('openedx.core.djangoapps.appsembler.tahoe_idp.helpers.pipeline_running', Mock(return_value=True))
def test_get_idp_form_url_for_register_with_pipeline(settings):
    """
    A running pipeline means a user already coming from Third Party Auth.

    Upon registration, Open edX  auto-submits the frontend hidden registration form.
    Returning, None to avoid breaking an otherwise needed form submit.
    """
    settings.FEATURES = {'ENABLE_THIRD_PARTY_AUTH': True}
    with override_site_config('admin', ENABLE_TAHOE_IDP=True):
        url = helpers.get_idp_form_url(None, 'register', '/home')
    assert not url, 'Return no URL when there is a running pipeline'


@pytest.mark.django_db
def test_store_idp_metadata_in_user_profile():
    """
    Ensure store_idp_metadata_in_user_profile saves metadata in User.profile.
    """
    learner = UserFactory()
    helpers.store_idp_metadata_in_user_profile(learner, {'custom_field': 'some value'})
    assert learner.profile.get_meta() == {'tahoe_idp_metadata': {'custom_field': 'some value'}}


@pytest.mark.django_db
def test_is_studio_allowed_for_user_superuser():
    """
    Verify that is_studio_allowed_for_user returns <True> for superusers
    """
    # We're not using user_with_org fixture to test users with no linked organization
    user = UserFactory.create(is_superuser=True)
    assert helpers.is_studio_allowed_for_user(user)


@pytest.mark.django_db
def test_is_studio_allowed_for_user_staff():
    """
    Verify that is_studio_allowed_for_user returns <True> for staff users
    """
    # We're not using user_with_org fixture to test users with no linked organization
    user = UserFactory.create(is_staff=True)
    assert helpers.is_studio_allowed_for_user(user)


@pytest.mark.django_db
def test_is_studio_allowed_for_user_organization_admin(user_with_org):
    """
    Verify that is_studio_allowed_for_user returns <True> for organization admins
    """
    user, organization = user_with_org
    tahoe_sites_apis.update_admin_role_in_organization(user, organization, set_as_admin=True)
    assert helpers.is_studio_allowed_for_user(user, organization)


@pytest.mark.django_db
def test_is_studio_allowed_for_user_staff_role(user_with_org):
    """
    Verify that is_studio_allowed_for_user returns <True> for users having <OrgStaffRole>
    """
    user, organization = user_with_org
    OrgStaffRole(organization.short_name).add_users(user)
    assert helpers.is_studio_allowed_for_user(user, organization)


@pytest.mark.django_db
def test_is_studio_allowed_for_user_instructor_role(user_with_org, client):
    """
    Verify that is_studio_allowed_for_user returns <True> for users having <OrgInstructorRole>
    """
    user, organization = user_with_org
    OrgInstructorRole(organization.short_name).add_users(user)
    assert helpers.is_studio_allowed_for_user(user, organization)


@pytest.mark.django_db
@pytest.mark.parametrize('role_class', [
    CourseCreatorRole,
    CourseInstructorRole,
    CourseStaffRole,
])
def test_is_studio_allowed_for_course_instructor(user_with_org, role_class):
    """
    Verify CourseInstructorRole is allowed via is_studio_allowed_for_user.
    """
    instructor, organization = user_with_org
    CourseAccessRole.objects.create(user=instructor, role=role_class.ROLE)
    assert helpers.is_studio_allowed_for_user(instructor, organization)


@pytest.mark.django_db
def test_is_studio_allowed_for_user_learner(user_with_org):
    """
    Verify that is_studio_allowed_for_user returns <False> for normal users
    """
    learner, organization = user_with_org
    assert not helpers.is_studio_allowed_for_user(learner, organization)


@pytest.mark.django_db
def test_is_studio_allowed_for_user_learner_no_organization(user_with_org):
    """
    Verify that is_studio_allowed_for_user will fetch the organization if not provided
    """
    learner, _ = user_with_org
    assert not helpers.is_studio_allowed_for_user(learner)


def test_is_studio_login_form_overridden_flag_not_available():
    """
    Verify that the default for not having the flag is to return <False>
    """
    assert 'TAHOE_IDP_STUDIO_LOGIN_FORM_OVERRIDE' not in settings.FEATURES
    assert not helpers.is_studio_login_form_overridden()


@pytest.mark.parametrize('flag_value,expected_result', [
    (None, False), (False, False), (True, True), ('something', True)
])
def test_is_studio_login_form_overridden_flag_available(flag_value, expected_result):
    """
    Verify that is_studio_login_form_overridden returns the value of the helper
    """
    with patch.dict('django.conf.settings.FEATURES', {'TAHOE_IDP_STUDIO_LOGIN_FORM_OVERRIDE': flag_value}):
        assert helpers.is_studio_login_form_overridden() is expected_result


@pytest.mark.parametrize('url', [
    'course-v1:ninja_org+course+2022',
    '/course-v1:ninja_org+course+2022',
    'bla_bla_bla/course-v1:ninja_org+course+2022/',
    'course-v1:ninja_org+course+2022/bla_bla_bla',
    'bla_bla_bla/course-v1:ninja_org+course+2022/bla_bla_bla',
    'bla_bla_bla/course-v1:ninja_org+course+2022/bla_bla_bla-v1:ninja_org+course+2022',
    'bla_bla_bla/course-v1:ninja_org+course+2022/bla_bla_bla/course-v1:ninja_org+course+2022',
    'bla_bla_bla/course-v1:unexpected_other_org+course+2022/bla_bla_bla/course-v1:ninja_org+course+2022/bla_bla_bla',
])
@pytest.mark.django_db
def test_extract_organization_from_url_success(url):
    """
    Verify that extract_organization_from_url returns the expected organization or None according to the given URL
    """
    organization = OrganizationFactory.create(short_name='ninja_org', name='ninja_org_long_name')
    assert helpers.extract_organization_from_url(url) == organization
    url = url.replace('course-v1', 'block-v1')
    assert helpers.extract_organization_from_url(url) == organization


@pytest.mark.parametrize('url', [
    'course-v1:ninja_org+course+',
    'course-v1:ninja_org+course',
    'course-v2:ninja_org+course+2022',
    'courses-v1:ninja_org+course+2022',
    'asdasdcourse-v1:ninja_org+course+2022',
    'asdasdcourse-v1:ninja_org+course+2022asdasdad',
    'bla_bla_bla/course-v1:ninja_org+course+2022/bla_bla_bla/course-v1:unexpected_other_org+course+2022/bla_bla_bla',
])
@pytest.mark.django_db
def test_extract_organization_from_url_not_found(url):
    """
    Verify that extract_organization_from_url returns the expected organization or None according to the given URL
    """
    # just to verify that the function doesn't return (None) because of a missing organization
    OrganizationFactory.create(short_name='ninja_org', name='ninja_org_long_name')

    assert helpers.extract_organization_from_url(url) is None


def test_get_redirect_to_lms_login_url_no_request():
    """
    Verify that get_redirect_to_lms_login_url will return empty string if no request is provided
    """
    assert helpers.get_redirect_to_lms_login_url(None) == ''


@pytest.mark.django_db
def test_get_redirect_to_lms_login_url_no_next(valid_request):
    """
    Verify that get_redirect_to_lms_login_url will return empty string if no request is provided
    """
    assert helpers.get_redirect_to_lms_login_url(valid_request) == ''


@pytest.mark.django_db
def test_get_redirect_to_lms_login_url_next_with_no_course(valid_request):
    """
    Verify that get_redirect_to_lms_login_url will return empty string if no request is provided
    """
    valid_request.GET['next'] = 'bla_bla'
    assert helpers.get_redirect_to_lms_login_url(valid_request) == ''


@pytest.mark.django_db
def test_get_redirect_to_lms_login_url_next_with_invalid_course(valid_request):
    """
    Verify that get_redirect_to_lms_login_url will return empty string if no request is provided
    """
    valid_request.GET['next'] = 'course/course-v1:ORG+DoesNotExist'
    assert helpers.get_redirect_to_lms_login_url(valid_request) == ''


@pytest.mark.django_db
def test_get_redirect_to_lms_login_url_next_with_valid_course(valid_request, user_with_org):
    """
    Verify that get_redirect_to_lms_login_url will return the expected URL is a valid course_id is provided
    """
    _, organization = user_with_org
    site = tahoe_sites_apis.get_site_by_organization(organization=organization)

    next_url = 'container/block-v1:{org}+course+run'.format(org=organization.short_name)
    encoded_next = parse.quote_plus(next_url)
    expected_url = 'http://{site_domain}/studio/?next={encoded_next}'.format(
        site_domain=site.domain,
        encoded_next=encoded_next
    )

    valid_request.GET['next'] = next_url
    assert helpers.get_redirect_to_lms_login_url(valid_request) == expected_url
