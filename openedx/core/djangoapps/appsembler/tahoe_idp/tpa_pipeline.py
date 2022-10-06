"""
Pipeline steps for Third Party Auth to support tahoe-idp package.
"""
import logging

import beeline
import tahoe_sites.api


from tahoe_idp import api as tahoe_idp_api

from . import course_roles
from .helpers import store_idp_metadata_in_user_profile
from .constants import TAHOE_IDP_BACKEND_NAME

log = logging.getLogger(__name__)


@beeline.traced(name='tpa_pipeline.tahoe_idp_user_updates')
def tahoe_idp_user_updates(auth_entry, strategy, details, user=None, *args, **kwargs):
    """
    Update the user after login via the Tahoe IdP backend.

    Performs the following updates:
     - Update the user `is_admin` status
     - Set OrgStaffRole for eligible users
     - Share Tahoe User.id with the `tahoe-idp` provider
     - Store the user metadate from the `tahoe-idp` into the `User.profile.meta`

    This pipeline step links both `tahoe-idp` and `tahoe-sites` packages.
    Although unlikely, updates to either modules may break this step.
    """
    backend_name = strategy.request.backend.name
    beeline.add_context_field('backend_name', backend_name)
    beeline.add_context_field('pipeline_details', details)

    if user and backend_name == TAHOE_IDP_BACKEND_NAME:
        set_as_admin = details['tahoe_idp_is_organization_admin']
        set_as_organization_staff = details['tahoe_idp_is_organization_staff']
        set_as_course_author = details['tahoe_idp_is_course_author']

        organization = tahoe_sites.api.get_current_organization(strategy.request)

        organization_short_name = organization.short_name
        beeline.add_context_field('organization_short_name', organization_short_name)

        tahoe_sites.api.update_admin_role_in_organization(
            user=user,
            organization=organization,
            set_as_admin=set_as_admin,
        )

        course_roles.update_organization_staff_roles(
            user=user,
            organization_short_name=organization_short_name,
            set_as_course_author=set_as_course_author,
            set_as_organization_staff=set_as_organization_staff,
        )

        store_idp_metadata_in_user_profile(user, details['tahoe_idp_metadata'])

        # TODO: Directly call `tahoe_idp.api` function may not be a good idea, find a better signal or hook instead.
        tahoe_idp_api.update_tahoe_user_id(user)
