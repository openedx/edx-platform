"""
Integration helpers for SiteConfig Client adapter.
"""

import logging
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

import tahoe_sites.api
from site_config_client.openedx.features import (
    is_feature_enabled_for_site,
    enable_feature_for_site,
)
from site_config_client.openedx.adapter import SiteConfigAdapter
from site_config_client.exceptions import SiteConfigurationError


log = logging.getLogger(__name__)

from ..preview.helpers import is_preview_mode


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


def get_active_site_uuids_from_site_config_service():
    """
    Get active Tier organization UUIDs via the client of the Site Configuration service.

    Return a list of UUID objects.
    """
    client = getattr(settings, 'SITE_CONFIG_CLIENT', None)
    if client:
        try:
            active_sites_response = client.list_active_sites()
            active_sites = active_sites_response['results']
            site_uuids = [UUID(site['uuid']) for site in active_sites]
            return site_uuids
        except SiteConfigurationError:
            log.exception('An error occurred while fetching site config active sites, returning an empty list.')

    return []


def get_configuration_adapter_status(current_request=None):
    """
    Get the live/draft status for the site configuration adapter.
    """
    if is_preview_mode(current_request):
        return 'draft'
    else:
        return 'live'


def get_configuration_adapter(site, status=None):
    """
    Get the configuration adapter with the current
    """
    if not status:
        status = get_configuration_adapter_status()
    uuid = tahoe_sites.api.get_uuid_by_site(site)
    return SiteConfigAdapter(site_uuid=uuid, status=status)
