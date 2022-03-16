"""
Integration helpers for SiteConfig Client adapter.
"""

from django.core.exceptions import ObjectDoesNotExist

import tahoe_sites.api

from site_config_client.openedx.features import (
    is_feature_enabled_for_site,
    enable_feature_for_site,
)
from site_config_client.openedx.adapter import SiteConfigAdapter

# TODO: Move these helpers into the `site_config_client.openedx.api` module


def is_enabled_for_site(site):
    """
    Checks if the SiteConfiguration client is enabled for a specific organization.
    """
    from django.conf import settings  # Local import to avoid AppRegistryNotReady error

    if site.id == settings.SITE_ID:
        # Disable the SiteConfig service on main site.
        return False

    try:
        uuid = tahoe_sites.api.get_uuid_by_site(site)
    except ObjectDoesNotExist:
        # Return sane result in case of malformed data
        return False
    return is_feature_enabled_for_site(uuid)


def enable_for_site(site):
    uuid = tahoe_sites.api.get_uuid_by_site(site)
    enable_feature_for_site(uuid)


def get_configuration_adapter(site):
    uuid = tahoe_sites.api.get_uuid_by_site(site)
    return SiteConfigAdapter(uuid)
