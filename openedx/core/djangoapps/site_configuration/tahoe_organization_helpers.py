"""
Helpers to support TAHOE_SITE_CONFIG_CLIENT_ORGANIZATIONS_SUPPORT feature.

TAHOE_SITE_CONFIG_CLIENT_ORGANIZATIONS_SUPPORT is an on by-default feature in production.
It uses `short_name` lookup instead of looking up by `course_org_filter`.

Although organization.short_name is more reliable and faster than `course_org_filter`, the best way to identify
an organization is via its Site UUID.

This module is a patch to the SiteConfiguration organization helpers across Open edX e.g. `get_value_for_org()`.

Purpose:
 - Provide compatibility with the Site Configuration Client.
 - Filter by organizations with active subscription.
"""

from organizations.models import Organization
import tahoe_sites.api


def get_all_orgs():
    """
    This returns active of the orgs that are considered in site configurations, This can be used,
        for example, to do filtering.

        Returns:
            A set of active organizations present in site configuration.

    Unlike the upstream method, this is compatible with the Site Configuration Client.
    """
    from openedx.core.djangoapps.appsembler.sites import utils as site_utils
    return site_utils.get_active_organizations().values_list('short_name', flat=True)


def get_configuration_for_org(org):
    """
    Get the SiteConfiguration for a specific organization by its short_name.

    Unlike the upstream method, this is compatible with the Site Configuration Client.
    """
    organization = Organization.objects.get(short_name=org)
    site = tahoe_sites.api.get_site_by_organization(organization)
    return site.configuration
