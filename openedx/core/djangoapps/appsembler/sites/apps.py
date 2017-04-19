from django.apps import AppConfig

from django.db.models.signals import pre_save, post_save
from django.contrib.sites.models import Site


class SitesConfig(AppConfig):
    name = 'openedx.core.djangoapps.appsembler.sites'
    label = 'appsembler_sites'

    def ready(self):
        from .models import patched_clear_site_cache

        pre_save.connect(patched_clear_site_cache, sender='site_configuration.SiteConfiguration')
