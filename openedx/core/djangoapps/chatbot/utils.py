from django.conf import settings
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from django.contrib.sites.models import Site

def get_site_config(domain, setting_name, default_value=None):
    try:
        site = Site.objects.get(domain=domain)
        site_config = SiteConfiguration.objects.get(site=site)
        return site_config.get_value(setting_name, default_value)
    except Exception as e:
        print(str(e))
        return None
    

