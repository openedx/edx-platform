"""
Tahoe 1.0 --> Tahoe 2.0 site migration.
"""
import uuid
from logging import getLogger

import tahoe_sites.api
from django.contrib.sites.models import Site

from openedx.core.djangoapps.appsembler.tahoe_tiers.legacy_amc_helpers import get_amc_tier_info

from .fusionauth_migration import (
    get_fa_api_client,
    migrate_user_to_fa,
)

from .site_config_migration import (
    migrate_site_configs,
)


log = getLogger(__name__)


def migrate_site(site_data):
    log.info('migrating site with %s', site_data)

    domain = site_data['site_domain']
    fusionauth_tenant_id = site_data['idp_tenant_id']
    fusionauth_application_id = site_data['idp_application_id']
    migrate_theme = site_data['migrate_theme']

    site = Site.objects.get(domain=domain)
    site_uuid = tahoe_sites.api.get_uuid_by_site(site)
    tier_info = get_amc_tier_info(site_uuid)

    assert uuid.UUID(fusionauth_tenant_id), 'Validate uuid'
    assert uuid.UUID(fusionauth_application_id), 'Validate uuid'

    api_client = get_fa_api_client(fusionauth_tenant_id)

    fusionauth_application_configs = api_client.retrieve_oauth_configuration(fusionauth_application_id)
    assert fusionauth_application_configs.was_successful(), 'Failed to get FusionAuth OAuth secret'

    app_config_json = fusionauth_application_configs.response.json()
    fusionauth_application_secret = app_config_json['oauthConfiguration']['clientSecret']

    migrate_site_configs(
        site_uuid=site_uuid,
        tier_info=tier_info,
        fa_tenant_id=fusionauth_tenant_id,
        fa_app_id=fusionauth_application_id,
        fa_app_secret=fusionauth_application_secret,
        migrate_theme=migrate_theme,
    )

    organization = tahoe_sites.api.get_organization_by_site(site)

    users = tahoe_sites.api.get_users_of_organization(
        organization=organization,
        without_inactive_users=True,
        without_site_admins=False,
    )

    for user in users:
        log.info('migrating %s in site %s', user.email, site.domain)
        migrate_user_to_fa(api_client=api_client, user=user, organization=organization)
