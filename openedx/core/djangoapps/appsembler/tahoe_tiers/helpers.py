"""
Tiers Tahoe helpers.
"""

import beeline

from tahoe_sites.api import get_uuid_by_organization

from ..sites.site_config_client_helpers import get_current_site_config_tier_info

from .legacy_amc_helpers import get_amc_tier_info


TIER_INFO_REQUEST_FIELD_NAME = '_tahoe_tier_info'


@beeline.traced('tahoe_tiers.helpers.get_tier_info')
def get_tier_info(request):
    """
    Get TierInfo either for both Tahoe 1.0 (AMC Postgres Tiers) and Tahoe 2.0 (SiteConfig service).
    """
    tier_info = getattr(request, TIER_INFO_REQUEST_FIELD_NAME, None)  # Get request-cached tier-info
    if not tier_info:
        # Try AMC tiers first, to ensure the least feature/performance impact on Tahoe 1.0 sites.
        organization = request.session.get('organization')
        beeline.add_context_field('organization', organization)
        if organization:
            site_uuid = get_uuid_by_organization(organization)
            tier_info = get_amc_tier_info(site_uuid=site_uuid)
        else:
            beeline.add_context_field("tiers.no_organization", True)

        if tier_info:
            beeline.add_context_field('amc_tier_info_used', True)

    if not tier_info:
        # If no tier info exists, try with the Site Configuration service tier info
        tier_info = get_current_site_config_tier_info()
        if tier_info:
            beeline.add_context_field('site_config_tier_info_used', True)

    if not tier_info:
        beeline.add_context_field('no_tier_info', True)

    setattr(request, TIER_INFO_REQUEST_FIELD_NAME, tier_info)
    return tier_info
