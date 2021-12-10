"""
Integration helpers for SiteConfig Client adapter.
"""

try:
    from site_config_client.openedx.features import is_feature_enabled_for_site
    from site_config_client.openedx.adapter import SiteConfigAdapter

    CONFIG_CLIENT_INSTALLED = True
except ImportError:
    CONFIG_CLIENT_INSTALLED = False

    def is_feature_enabled_for_site(site_uuid):
        """
        Dummy helper.
        """
        return False

    class SiteConfigAdapter:
        """
        Dummy SiteConfigAdapter.
        """
        def __init__(self, site_uuid):
            self.site_uuid = site_uuid


def is_enabled_for_current_organization():
    """
    Checks if the SiteConfiguration client is enabled for a specific organization.
    """
    if not CONFIG_CLIENT_INSTALLED:
        return False

    from . import utils as site_utils  # Local import to avoid AppRegistryNotReady error
    organization = site_utils.get_current_organization()
    return is_feature_enabled_for_site(organization.edx_uuid)


def get_current_configuration_adapter():
    if not CONFIG_CLIENT_INSTALLED:
        return None

    from . import utils as site_utils  # Local import to avoid AppRegistryNotReady error
    organization = site_utils.get_current_organization()
    return SiteConfigAdapter(organization.edx_uuid)
