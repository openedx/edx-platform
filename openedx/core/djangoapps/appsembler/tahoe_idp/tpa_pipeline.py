"""
Pipeline steps for Third Party Auth to support tahoe-idp package.
"""
import logging

import beeline
import tahoe_sites.api

from openedx.core.djangoapps.appsembler.auth import course_roles

from .constants import TAHOE_IDP_BACKEND_NAME

log = logging.getLogger(__name__)


@beeline.traced(name='tpa_pipeline.set_roles_from_tahoe_idp_roles')
def set_roles_from_tahoe_idp_roles(auth_entry, strategy, details, user=None, *args, **kwargs):
    """
    Update the user `is_admin` status and OrgStaffRole when using the `tahoe-idp` backend.

    This pipeline step links both `tahoe-idp` and `tahoe-sites` packages.
    Although unlikely, updates to either modules may break this step.
    """
    backend_name = strategy.request.backend.name
    beeline.add_context_field('backend_name', backend_name)
    beeline.add_context_field('pipeline_details', details)

    if user and backend_name == TAHOE_IDP_BACKEND_NAME:
        set_as_admin = details['tahoe_idp_is_organization_admin']
        set_as_organization_staff = details['tahoe_idp_is_organization_staff']

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
            set_as_organization_staff=set_as_organization_staff,
        )
