"""
Migration script to migrate existing data from SiteConfiguration model to Site Configuration service.
"""
from logging import getLogger

from django.conf import settings
from tahoe_sites.api import get_organization_by_uuid, get_site_by_uuid
from site_config_client.models import SiteConfigClientEnabled


log = getLogger(__name__)


CSS_REPLACEMENT = {
    # Tahoe 1.0 var --> Tahoe 2.0 var
    '$brand-primary-color': '$primary_brand_color',
    '$brand-accent-color': '$buttons_accents_color',
    '$cta-button-text-color': '$buttons_text_color',
    '$base-text-color': '$text_color',
    '$primary-font-name': '$selected_font',
    '$header-logo-height': '$header_logo_height',
    '$header-font-size': '$header_font_size',
    '$header-bg-color': '$header_background_color',
    '$header-text-color': '$header_text_color',
    '$navbar-button-bg': '$header_buttons_color',
    'UNKNOWN_TAHOE1_VAR#1': '$header_buttons_text_color',  # TODO: Ask Matej
    '$footer-logo-width': '$footer_logo_width',
    'UNKNOWN_TAHOE1_VAR#2': '$footer_font_size',  # TODO: Ask Matej
    '$footer-bg-color': '$footer_background_color',
    '$footer-text-color': '$footer_text_color',
    '$footer-link-color': '$footer_links_color',
    '$footer-copyright-text-color': '$footer_copyright_text_color',
}


def override_configs(
        client,
        site_uuid,
        configs,
        fa_tenant_id,
        fa_app_id,
        fa_app_secret,
        migrate_theme,
):
    """
    Uses Configuration Override Endpoint:

    PUT /v0/configuration-override/<site_uuid>/

    content_type = application/json
    body = {
          "author_email": "test@example.com",
          "css": [{
              "name": "$brand-primary-color",
              "value": ["rgba(0,1,1,1)", "rgba(0,1,1,1)"]
          }, {
              "name": "$brand-shadow-color",
              "value": ["rgba(0,1,1,1)", "rgba(0,1,1,1)"]
          }]
        }
    """
    segment_key_name = 'SEGMENT_KEY'
    secret = [{
        "name": "TAHOE_IDP_CLIENT_SECRET",
        "value": fa_app_secret,
    }]

    # Segment key should be in secrets
    segment_key = configs.site_values.pop(segment_key_name, None)
    if segment_key:
        secret.append({'name': 'SEGMENT_KEY', 'value': segment_key})
    setting = [
        {'name': k, 'value': v}
        for k, v in configs.site_values.items()
    ]
    setting.append({
        'name': 'THEME_VERSION',
        'value': 'tahoe-v2',
    })

    css = []
    page = []
    if migrate_theme:
        css = [
            {'name': tahoe2_var, 'value': configs.sass_variables[tahoe1_var][1]}
            for tahoe1_var, tahoe2_var in CSS_REPLACEMENT.items()
            if tahoe1_var in configs.sass_variables
        ]
        page = [
            {'name': k, 'value': v} for k, v in configs.page_elements.items()
        ]

    configs_override = {
        "author_email": "omar@appsembler.com",
        "setting": setting,
        "css": css,
        "page": page,
        "secret": secret,
        "admin": [
            {
                "name": "ENABLE_TAHOE_IDP",
                "value": True,
            },
            {
                "name": "TAHOE_IDP_TENANT_ID",
                "value": fa_tenant_id,
            },
            {
                "name": "TAHOE_IDP_CLIENT_ID",
                "value": fa_app_id,
            },
        ]
    }
    log.info('configs overridden %s', client.override_configs(site_uuid, configs_override))


def migrate_site_configs(site_uuid, tier_info, fa_tenant_id, fa_app_id, fa_app_secret, migrate_theme):
    """
    1. Create site v1/site/
        - get Organization.edx_uuid for site
        - pass the edx_uuid
    2. Get existing config data for site
    3. Migrate existing config data via v0/configuration-override/site_uuid
    """
    client = settings.SITE_CONFIG_CLIENT
    site = get_site_by_uuid(site_uuid)
    organization = get_organization_by_uuid(site_uuid)
    configs = site.configuration
    domain = site.domain

    # 1. create the site in Site Config service
    response = client.create_site(domain_name=site.domain, site_uuid=str(site_uuid), params={
        'tier': tier_info.tier,
        'subscription_ends': str(tier_info.subscription_ends),
        'always_active': tier_info.always_active,
    })
    log.info('Site created: %s %s', site.domain, response)

    override_configs(
        client=client,
        site_uuid=site_uuid,
        configs=configs,
        fa_tenant_id=fa_tenant_id,
        fa_app_id=fa_app_id,
        fa_app_secret=fa_app_secret,
        migrate_theme=migrate_theme,
    )

    # 3. switch to site config service by enabling site in SiteConfigClientEnabled model
    note = 'domain = {domain} , organization name = {short_name} -- (migrated from tahoe 1.0).'.format(
        domain=domain,
        short_name=organization.short_name,
    )
    enabled_site = SiteConfigClientEnabled.objects.create(site_uuid=site_uuid, note=note)
    log.info('enabled site %s', enabled_site)

    configs.site_values = {}
    configs.save()
