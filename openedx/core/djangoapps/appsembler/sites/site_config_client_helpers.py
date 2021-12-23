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


def get_single_org_for_site(site):
    """
    Gets a single organization for a site.

    Raises:
        Organization.DoesNotExist
        Organization.MultipleObjectsReturned
    """
    return site.organizations.get()


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

    organization = get_single_org_for_site(site)
    return is_feature_enabled_for_site(organization.edx_uuid)


def get_configuration_adapter(site):
    if not CONFIG_CLIENT_INSTALLED:
        return None

    organization = get_single_org_for_site(site)
    return SiteConfigAdapter(organization.edx_uuid)
