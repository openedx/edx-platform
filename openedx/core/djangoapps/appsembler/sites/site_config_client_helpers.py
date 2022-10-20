"""
Integration helpers for SiteConfig Client adapter.
"""
import beeline
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

from tiers.tier_info import TierInfo

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from ..preview.helpers import is_preview_mode


log = logging.getLogger(__name__)


# TODO: Move these helpers into the `site_config_client.openedx.api` module


@beeline.traced('site_config_client_helpers.is_enabled_for_site')
def is_enabled_for_site(site):
    """
    Checks if the SiteConfiguration client is enabled for a specific organization.
    """
    from django.conf import settings  # Local import to avoid AppRegistryNotReady error

    is_enabled = False
    if site.id != settings.SITE_ID:  # Disable the SiteConfig service on main site.
        try:
            uuid = tahoe_sites.api.get_uuid_by_site(site)
        except ObjectDoesNotExist:
            # Act as if disabled in case of malformed data
            is_enabled = False
        else:
            is_enabled = is_feature_enabled_for_site(uuid)

    beeline.add_trace_field('site_config.enabled', is_enabled)
    return is_enabled


def enable_for_site(site, note=''):
    uuid = tahoe_sites.api.get_uuid_by_site(site)
    enable_feature_for_site(uuid, note=note)


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


def get_current_site_config_tier_info():
    """
    Return TierInfo object from SiteConfiguration backend configs.
    """
    tier_info = None
    api_adapter = get_current_configuration_adapter()
    if api_adapter:
        current_site_info = api_adapter.get_site_info()
        tier_info = TierInfo(
            tier=current_site_info['tier'],
            subscription_ends=current_site_info['subscription_ends'],
            always_active=current_site_info['always_active'],
        )

    return tier_info


def get_configuration_adapter_status(current_request=None):
    """
    Get the live/draft status for the site configuration adapter.
    """
    if is_preview_mode(current_request):
        return 'draft'
    else:
        return 'live'


def init_site_configuration_adapter(site, status=None):
    """
    Get the configuration adapter for a specific status (live/draft).

    This method is expensive and used for initialization.
    """
    if not status:
        status = get_configuration_adapter_status()
    uuid = tahoe_sites.api.get_uuid_by_site(site)
    return SiteConfigAdapter(site_uuid=uuid, status=status)


def get_current_configuration_adapter():
    """
    Get the SiteConfigAdapter from the current site configuration.

    This method returns `None` in celery tasks.
    """
    site_config_model = configuration_helpers.get_current_site_configuration()
    if site_config_model:
        return site_config_model.api_adapter
    else:
        return None
