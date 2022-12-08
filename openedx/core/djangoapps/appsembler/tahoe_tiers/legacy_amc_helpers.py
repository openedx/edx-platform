"""
A module for deprecated AMC tier utilities.

TODO: Remove this module once AMC is shut down. Related to RED-2845 too
"""

import logging
import beeline
from uuid import UUID

from django.utils import timezone

from tiers.models import Tier
from ..tahoe_tiers.tier_info import TierInfo


log = logging.getLogger(__name__)


@beeline.traced('legacy_amc_helpers.get_amc_tier_info')
def get_amc_tier_info(site_uuid):  # pragma: no cover
    """
    Get TierInfo for an AMC-enabled (Tahoe 1.0) site.

    Hack: This queries the django-tier database in a rather hacky way.

    WARNING: !! This function is _not_ fully covered with tests. Please edit with caution and test on staging. !!
    """
    try:
        site_uuid_hex = UUID(str(site_uuid)).hex

        # Query the AMC Postgres database directly
        tiers = Tier.objects.raw(
            """SELECT
                   t.id as id,
                   t.name AS name,
                   t.tier_expires_at AS tier_expires_at,
                   org.edx_uuid as edx_uuid,
                   t.tier_enforcement_exempt AS tier_enforcement_exempt
               FROM tiers_tier as t
               INNER JOIN organizations_organization as org on t.organization_id = org.id
               WHERE org.edx_uuid = %s
               LIMIT 1
            """,
            [str(site_uuid_hex)]
        )
        tiers_list = list(tiers)

        if not tiers_list:
            # If the organization has no AMC-tier fail silently and log it in honeycomb.
            # This either happens in the case of a Tahoe 2.0 site or a missing tier
            # from AMC (although that shouldn't happen).
            beeline.add_context_field("tiers.organization_without_tier", True)
            return None

        tier = tiers[0]
        return TierInfo(
            tier=tier.name,
            subscription_ends=tier.tier_expires_at,
            always_active=tier.tier_enforcement_exempt,
        )
    except Exception:  # noqa
        log.exception('Error with fetching the tier from AMC')
        beeline.add_context_field("tiers.exception_with_tier", True)
        log.exception("Organization has a problem with its Tier: {0}".format(site_uuid))
        return None


def get_active_tiers_uuids_from_amc_postgres():  # pragma: no cover
    """
    Get active Tier organization UUIDs from the Tiers (AMC Postgres) database.

    Hack: This queries the django-tier database in a rather hacky way.

    Return a list of UUID objects.

    WARNING: !! This function is _not_ fully covered with tests. Please edit with caution and test on staging. !!
    """
    # This queries the AMC Postgres database
    tiers = Tier.objects.raw(
        """
        SELECT
            t.id as id,
            org.edx_uuid as site_uuid
        FROM tiers_tier as t
        INNER JOIN organizations_organization as org on t.organization_id = org.id
        WHERE t.tier_expires_at >= %s OR t.tier_enforcement_exempt
        """,
        [str(timezone.now())]
    )

    return [
        UUID(t.site_uuid)
        for t in tiers
    ]
