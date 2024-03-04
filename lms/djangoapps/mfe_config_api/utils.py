from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


def get_mfe_config_for_site(request=None, site=None, mfe=None):
    site_configuration = None
    if request or site:
        if not site:
            site_domain = request.META.get("HTTP_X_FORWARDED_HOST", settings.LMS_BASE)
            site_domain = site_domain.replace("apps.", "")
        else:
            site_domain = site.domain
        try:
            site_configuration = SiteConfiguration.objects.get(site__domain=site_domain)
            if site_configuration.get_value("MFE_CONFIG"):
                mfe_config = site_configuration.get_value("MFE_CONFIG")
            else:
                mfe_config = configuration_helpers.get_value('MFE_CONFIG', settings.MFE_CONFIG)
        except SiteConfiguration.DoesNotExist:
            mfe_config = configuration_helpers.get_value('MFE_CONFIG', settings.MFE_CONFIG)

        if request:
            if not mfe:
                if getattr(request, "query_params", None):
                    mfe = str(request.query_params.get("mfe"))
                else:
                    mfe = request.GET.get("mfe")

            if mfe:
                if site_configuration and site_configuration.get_value("MFE_CONFIG_OVERRIDES"):
                    app_config = site_configuration.get_value("MFE_CONFIG_OVERRIDES")
                else:
                    app_config = configuration_helpers.get_value(
                        'MFE_CONFIG_OVERRIDES',
                        settings.MFE_CONFIG_OVERRIDES,
                    )
                mfe_config.update(app_config.get(mfe, {}))
    else:
        mfe_config = configuration_helpers.get_value('MFE_CONFIG', settings.MFE_CONFIG)
        if mfe:
            if site_configuration and site_configuration.get_value("MFE_CONFIG_OVERRIDES"):
                app_config = site_configuration.get_value("MFE_CONFIG_OVERRIDES")
            else:
                app_config = configuration_helpers.get_value(
                    'MFE_CONFIG_OVERRIDES',
                    settings.MFE_CONFIG_OVERRIDES,
                )
            mfe_config.update(app_config.get(mfe, {}))
    return mfe_config
