"""
A module for deprecated AMC tier utilities.

TODO: Remove this module once AMC is shut down.
"""

from django.utils import timezone
from django.db.models import Q, F


def get_amc_tier_info_for_org(organization):
    """
    Get the Tier for the organization.

    Hack: This queries the django-tier database in a rather hacky way.
    """
    from tiers.models import Tier  # pylint: disable=import-error
    tier = Tier.objects.defer('organization').get(organization__edx_uuid=organization.edx_uuid)
    tier_object = Tier(
        name=tier.name,
        tier_enforcement_exempt=tier.tier_enforcement_exempt,
        tier_expires_at=tier.tier_expires_at,
        organization=organization,
    )
    return tier_object.get_tier_info()


def get_active_tiers_uuids_from_amc_postgres(now=None):
    """
    Get active Tier organization UUIDs from the Tiers (AMC Postgres) database.

    Note: This mostly a hack that's needed for improving the performance of
          batch operations by excluding dead sites.

    Return a list of UUID objects.
    """
    from tiers.models import Tier

    if not now:
        now = timezone.now()

    # This queries the AMC Postgres database
    active_tiers_uuids = Tier.objects.filter(
        Q(tier_enforcement_exempt=True) |
        Q(tier_expires_at__gte=now)
    ).annotate(
        organization_edx_uuid=F('organization__edx_uuid')
    ).values_list('organization_edx_uuid', flat=True)
    return list(active_tiers_uuids)
