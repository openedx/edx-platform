"""
Tests for `tahoe_idp.helpers`.
"""
from unittest.mock import patch, Mock

import pytest

from organizations.tests.factories import OrganizationFactory
from site_config_client.openedx.test_helpers import override_site_config
from tahoe_sites import api as tahoe_sites_apis

from openedx.core.djangoapps.appsembler.tahoe_idp import helpers
from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from student.roles import OrgInstructorRole, OrgStaffRole
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
    assert url == '/register-use-fa-form'


def test_get_idp_register_url_with_next():
    url = helpers.get_idp_register_url(next_url='/courses?per_page=10')
    assert url == '/register-use-fa-form?next=%2Fcourses%3Fper_page%3D10', 'should add encoded `next`'


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

    assert url == '/register-use-fa-form?next=%2Fhome', 'Return a URL when there is no running pipeline'


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
