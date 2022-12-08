import pytest

from tahoe_sites.zd_helpers import should_site_use_org_models
from ..legacy_amc_helpers import (
    get_amc_tier_info,
    get_active_tiers_uuids_from_amc_postgres,
)


@pytest.mark.django_db
def test_get_amc_tier_info_not_found():
    assert not get_amc_tier_info('6229db46-76e7-11ed-bb20-37f3f60d0442'), 'Non-existent tier info'


@pytest.mark.django_db
@pytest.mark.skipif(
    condition=not should_site_use_org_models(),
    reason='Needs AMC database compatible edx-organizations'
)
def test_get_amc_tier_info_found():
    from tiers.models import Tier
    from organizations.tests.factories import OrganizationFactory

    organization = OrganizationFactory.create(edx_uuid='2f51e0e1-7cd4-4447-86fc-5de03e2cf3b1')
    tier = Tier.objects.create(organization=organization)
    assert tier.organization == organization
    tier = get_amc_tier_info(organization.edx_uuid)
    assert tier, 'Should find tier'
    assert tier.tier == 'trial', 'Should be trial'


@pytest.mark.django_db
@pytest.mark.skipif(
    condition=not should_site_use_org_models(),
    reason='Needs AMC database compatible edx-organizations'
)
def test_active_tiers():
    from tiers.models import Tier
    from organizations.tests.factories import OrganizationFactory

    active_org = OrganizationFactory.create(edx_uuid='2f51e0e1-7cd4-4447-86fc-5de03e2cf3b1')
    Tier.objects.create(organization=active_org)

    inactive_org = OrganizationFactory.create(edx_uuid='9e29c034-76f1-11ed-a879-7702b938796e')
    Tier.objects.create(organization=inactive_org, tier_expires_at='2017-01-01')

    exempted_org = OrganizationFactory.create(edx_uuid='496efb30-76f2-11ed-b521-37e754be4889')
    Tier.objects.create(organization=exempted_org, tier_enforcement_exempt=True, tier_expires_at='2017-01-01')

    org_without_tier = OrganizationFactory.create(edx_uuid='e54d116e-76f1-11ed-b6c2-87cd9adfb48f')

    active_tier_uuids = get_active_tiers_uuids_from_amc_postgres()
    active_tier_uuids = [str(site_uuid) for site_uuid in active_tier_uuids]

    assert active_org.edx_uuid in active_tier_uuids, 'Should only list orgs with active tiers'
    assert exempted_org.edx_uuid in active_tier_uuids, 'Exempted orgs are considered active'
    assert inactive_org.edx_uuid not in active_tier_uuids, 'Expired org tier'
    assert org_without_tier.edx_uuid not in active_tier_uuids, 'Missing org tier should not appear here'
