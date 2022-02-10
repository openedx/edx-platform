"""
Integration helpers for SiteConfig Client adapter.
"""

import tahoe_sites.api

try:
    from site_config_client.openedx.features import (
        is_feature_enabled_for_site,
        enable_feature_for_site,
    )
    from site_config_client.openedx.adapter import SiteConfigAdapter

    CONFIG_CLIENT_INSTALLED = True
except ImportError:
    CONFIG_CLIENT_INSTALLED = False

    def is_feature_enabled_for_site(site_uuid):
        """
        Dummy helper.
        """
        return False

    def enable_feature_for_site(site_uuid):
        """
        Dummy helper.
        """
        pass

    class SiteConfigAdapter:
        """
        Dummy SiteConfigAdapter.
        """
        def __init__(self, site_uuid):
            self.site_uuid = site_uuid


def is_enabled_for_site(site):
    """
    Checks if the SiteConfiguration client is enabled for a specific organization.
    """
    if not CONFIG_CLIENT_INSTALLED:
        return False

    from django.conf import settings  # Local import to avoid AppRegistryNotReady error

    if site.id == settings.SITE_ID:
        # Disable the SiteConfig service on main site.
        return False

    uuid = tahoe_sites.api.get_uuid_by_site(site)
    return is_feature_enabled_for_site(uuid)


def enable_for_site(site):
    uuid = tahoe_sites.api.get_uuid_by_site(site)
    enable_feature_for_site(uuid)


def get_configuration_adapter(site):
    if not CONFIG_CLIENT_INSTALLED:
        return None

    uuid = tahoe_sites.api.get_uuid_by_site(site)
    return SiteConfigAdapter(uuid)
