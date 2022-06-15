"""
A module for deprecated AMC tier utilities.

TODO: Remove this module once AMC is shut down.
"""

import logging
import beeline

from django.utils import timezone
from django.db.models import Q, F

from tiers.models import Tier

log = logging.getLogger(__name__)


@beeline.traced('legacy_amc_helpers.get_amc_tier_info_from_organization')
def get_amc_tier_info_from_organization(organization):  # pragma: no cover
    """
    Get TierInfo for an AMC-enabled (Tahoe 1.0) site.

    Hack: This queries the django-tier database in a rather hacky way.

    WARNING: !! This function is _not_ covered with tests. Please edit with caution and test manually. !!
    """
    if not organization:
        beeline.add_context_field("tiers.no_organization", True)
        return None

    beeline.add_context_field("tiers.organization", "{}".format(organization))
    try:
        # Query the AMC Postgres database directly
        tier = Tier.objects.defer('organization').get(organization__edx_uuid=organization.edx_uuid)
        tier_info = tier.get_tier_info()
    except Exception:
        # If the organization for some reason does not have a tier assigned
        # fail silently. This should not happen. We should always automatically create
        # a tier for each organization.
        beeline.add_context_field("tiers.organization_without_tier", True)
        log.exception("Organization has a problem with its Tier: {0}".format(organization))
        return None

    return tier_info


def get_active_tiers_uuids_from_amc_postgres():  # pragma: no cover
    """
    Get active Tier organization UUIDs from the Tiers (AMC Postgres) database.

    Hack: This queries the django-tier database in a rather hacky way.

    Return a list of UUID objects.

    WARNING: !! This function is _not_ covered with tests. Please edit with caution and test manually. !!
    """
    # This queries the AMC Postgres database
    active_tiers_uuids = Tier.objects.filter(
        Q(tier_enforcement_exempt=True) |
        Q(tier_expires_at__gte=timezone.now())
    ).annotate(
        organization_edx_uuid=F('organization__edx_uuid')
    ).values_list('organization_edx_uuid', flat=True)
    return list(active_tiers_uuids)
