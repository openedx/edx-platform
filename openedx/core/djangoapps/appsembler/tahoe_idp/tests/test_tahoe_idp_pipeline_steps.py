"""
Tests for the `tahoe-idp` pipeline steps and settings.
"""
import pytest
from unittest.mock import patch, Mock
from django.conf import settings

import tahoe_sites.api

from common.djangoapps.student.roles import CourseCreatorRole, OrgStaffRole
from ..tpa_pipeline import tahoe_idp_user_updates

from openedx.core.djangoapps.site_configuration.tests.factories import SiteFactory
from common.djangoapps.student.tests.factories import UserFactory

from organizations.tests.factories import OrganizationFactory


def test_tahoe_idp_step_in_settings():
    """
    Test for SOCIAL_AUTH_PIPELINE setting to ensure the `tahoe_idp_user_updates` step is configured correctly.
    """
    idp_step_path = 'openedx.core.djangoapps.appsembler.tahoe_idp.tpa_pipeline.tahoe_idp_user_updates'
    force_sync_step_path = 'third_party_auth.pipeline.user_details_force_sync'
    # Release upgrade note: If this fails, it means upstream have updated Open edX significantly and we need
    #                       to review the setup of `tahoe_idp_user_updates`
    assert force_sync_step_path in settings.SOCIAL_AUTH_PIPELINE, 'Release upgrade: Sanity check upstream configs'

    # Check Tahoe-specific configs
    assert idp_step_path in settings.SOCIAL_AUTH_PIPELINE, 'The idp step should be added to SOCIAL_AUTH_PIPELINE'

    # Ensure we have the right order of pipeline steps
    # The idea is, it's only safe to update the information and trust if if the `user_details_force_sync` has been run
    # Before that, we may have incomplete registration
    idp_step_index = settings.SOCIAL_AUTH_PIPELINE.index(idp_step_path)
    force_sync_step_index = settings.SOCIAL_AUTH_PIPELINE.index(force_sync_step_path)
    assert idp_step_index == force_sync_step_index + 1, 'Tahoe IdP step should be right after `user_details_force_sync`'


@pytest.mark.parametrize('user_details,should_be_admin,should_be_staff,message', [
    (
        {
            'tahoe_idp_is_organization_admin': False,
            'tahoe_idp_is_organization_staff': False,
            'tahoe_idp_metadata': {'field': 'some value'},
        },
        False,
        False,
        'Check for learner',
    ),
    (
        {
            'tahoe_idp_is_organization_admin': False,
            'tahoe_idp_is_organization_staff': True,
            'tahoe_idp_metadata': {'field': 'some value'},
        },
        False,
        True,
        'Check for Studio',
    ),
    (
        {
            'tahoe_idp_is_organization_admin': True,
            'tahoe_idp_is_organization_staff': True,
            'tahoe_idp_metadata': {'field': 'some value'},
        },
        True,
        True,
        'Check for Admins',
    ),
])
@pytest.mark.django_db
def test_tahoe_idp_roles_step_roles(user_details, should_be_admin, should_be_staff, message):
    """
    Tests for happy scenarios of the `tahoe_idp_user_updates` step.
    """
    site = SiteFactory.create()
    organization = OrganizationFactory.create()
    tahoe_sites.api.create_tahoe_site_by_link(organization, site)
    user = UserFactory.create()
    tahoe_sites.api.add_user_to_organization(user, organization, is_admin=False)

    strategy = Mock()
    strategy.request.site = site
    strategy.request.backend.name = 'tahoe-idp'

    with patch('openedx.core.djangoapps.appsembler.tahoe_idp.tpa_pipeline.tahoe_idp_api', create=True) as tahoe_idp_api:
        tahoe_idp_user_updates(
            auth_entry=None,
            strategy=strategy,
            details=user_details,
            user=user,
        )

    org_role = OrgStaffRole(organization.short_name)
    creator_role = CourseCreatorRole()
    assert org_role.has_user(user) == should_be_staff, message
    assert creator_role.has_user(user) == should_be_staff, message
    assert tahoe_sites.api.is_active_admin_on_organization(user, organization) == should_be_admin, message
    assert user.profile.get_meta() == {'tahoe_idp_metadata': {'field': 'some value'}}
    tahoe_idp_api.update_tahoe_user_id.assert_called_once_with(user)


def test_tahoe_idp_roles_step_missing_details():
    """
    Missing user details should break the step.

    In real-world scenario this happens due to broken `tahoe-idp` backend.
    """
    strategy = Mock()
    strategy.request.backend.name = 'tahoe-idp'

    with pytest.raises(KeyError, match='tahoe_idp_is_organization_admin'):
        # tahoe_idp_is_organization_admin is missing from `user_details`
        tahoe_idp_user_updates(auth_entry=None, user=Mock(), strategy=strategy, details={
            'idp_is_organization_staff': False,
        })

    with pytest.raises(KeyError, match='tahoe_idp_is_organization_staff'):
        # tahoe_idp_is_organization_staff is missing from `user_details`
        tahoe_idp_user_updates(auth_entry=None, user=Mock(), strategy=strategy, details={
            'tahoe_idp_is_organization_admin': False,
        })


def test_idp_roles_step_missing_user():
    """
    Missing user or different backends should mean the step is skipped.

    This ensures compatibility with the SAML and other SSO backends.
    """
    strategy = Mock()
    strategy.request.backend.name = 'tahoe-idp'
    # Should skip the step if the user is missing
    tahoe_idp_user_updates(auth_entry=None, user=None, strategy=strategy, details={})

    strategy.request.backend.name = 'saml'
    # Should skip the step for `saml` and other non `tahoe-idp` backends
    tahoe_idp_user_updates(auth_entry=None, user=Mock(), strategy=strategy, details={})
