"""
Helper module for Tahoe Identity Provider package.

 - https://github.com/appsembler/tahoe-idp/
"""

from collections import OrderedDict
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlencode

from site_config_client.openedx import api as config_client_api

from tahoe_sites.api import is_active_admin_on_organization, get_organization_for_user
import third_party_auth
from third_party_auth.pipeline import running as pipeline_running


from .constants import (
    TAHOE_IDP_BACKEND_NAME,
    TAHOE_IDP_PROVIDER_NAME,
)

from student.roles import (
    CourseAccessRole,
    CourseCreatorRole,
    CourseInstructorRole,
    CourseStaffRole,
    OrgInstructorRole,
    OrgStaffRole,
)

from tahoe_idp import api as tahoe_idp_api


def is_tahoe_idp_enabled():
    """
    Tahoe: Check if tahoe-idp package is enabled for the current site (or cluster-wide).
    """
    global_flag = settings.FEATURES.get('ENABLE_TAHOE_IDP', False)
    return config_client_api.get_admin_value('ENABLE_TAHOE_IDP', default=global_flag)


def get_idp_logout_url():
    """
    Get Tahoe IdP URL.
    """
    if is_tahoe_idp_enabled():
        # This logs out from IdP first, then the IdP redirects to Open edX logout.
        post_logout_redirect_uri = config_client_api.get_setting_value('LMS_ROOT_URL')
        return tahoe_idp_api.get_logout_url(post_logout_redirect_uri=post_logout_redirect_uri)


def get_idp_login_url(next_url=None, auth_entry='login'):
    """
    Get Tahoe IdP login URL which uses `social_auth`.
    """
    params = OrderedDict()
    params['auth_entry'] = auth_entry
    if next_url:
        params['next'] = next_url

    base = reverse('social:begin', args=[TAHOE_IDP_BACKEND_NAME])
    return '{base}?{query}'.format(
        base=base,
        query=urlencode(params),
    )


def get_idp_register_url(next_url=None):
    """
    Get Tahoe IdP register URL using `tahoe-idp` package.
    """
    return get_idp_login_url(next_url=next_url, auth_entry='register')


def get_idp_form_url(request, initial_form_mode, next_url):
    """
    Get the login/register URLs for the identity provider.

    Disable upstream login/register forms when the Tahoe Identity Provider is enabled.
    """
    if not is_tahoe_idp_enabled():
        return None

    if not third_party_auth.is_enabled():
        return None

    auth_entry = 'login'
    if initial_form_mode == "register":
        auth_entry = 'register'

        if pipeline_running(request):
            # Upon registration, Open edX  auto-submits the frontend hidden registration form.
            # Returning, None to avoid breaking an otherwise needed form submit.
            return None

    return get_idp_login_url(next_url=next_url, auth_entry=auth_entry)


def store_idp_metadata_in_user_profile(user, metadata):
    """
    Store data from IdP into the User profile for later use.
    """
    meta = user.profile.get_meta()
    meta["tahoe_idp_metadata"] = metadata
    user.profile.set_meta(meta)
    user.profile.save()


def remove_tahoe_idp_from_account_settings(providers):
    """
    Remove the `tahoe-idp` entry from account settings.
    """
    return [
        provider for provider in providers
        if provider['id'] != TAHOE_IDP_PROVIDER_NAME
    ]


def deprecated_has_course_specific_role(user):
    """
    Check if the user has Studio access in a specific course.

    This is deprecated until Tahoe IdP migration is complete.

    Afterward, FusionAuth should control the roles and course-specific access should
    be handled there.

    TODO: RED-3139 remove this function after adding support for course-specific roles.
    """
    return CourseAccessRole.objects.filter(
        user=user,
        role__in=[
            CourseCreatorRole.ROLE,
            CourseInstructorRole.ROLE,
            CourseStaffRole.ROLE,
        ],
    )


def is_studio_allowed_for_user(user, organization=None):
    """
    Check whether the given user is permitted to log into studio or not

    Permission rules:
       The user is superuser
    OR the user is staff user
    OR the user is an admin on the organization
    OR the user has deprecated_has_course_specific_role()
    OR the user has (OrgStaffRole) or (OrgInstructorRole) role

    :param user: the user in question
    :param organization: the user's organization. If the user is not super admin or staff, this value will be used
        to question the rest of the rules. It'll also be fetched internally if not provided
    :return: <True> if permitted. <False> otherwise
    """
    if user.is_superuser or user.is_staff:
        return True

    if organization is None:
        organization = get_organization_for_user(user)

    if is_active_admin_on_organization(user=user, organization=organization):
        return True

    if deprecated_has_course_specific_role(user):
        return True

    short_name = organization.short_name
    has_org_wide_role = OrgStaffRole(short_name).has_user(user) or OrgInstructorRole(short_name).has_user(user)

    return has_org_wide_role


def is_studio_login_form_overridden():
    """
    Return the value of TAHOE_IDP_STUDIO_LOGIN_FORM_OVERRIDE. Default is <False>
    """
    if settings.FEATURES.get('TAHOE_IDP_STUDIO_LOGIN_FORM_OVERRIDE', None):
        return True
    return False
