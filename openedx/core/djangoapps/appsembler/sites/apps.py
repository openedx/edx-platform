from django.apps import AppConfig

from django.db.models.signals import pre_save, post_save


class SitesConfig(AppConfig):
    name = 'openedx.core.djangoapps.appsembler.sites'
    label = 'appsembler_sites'

    def ready(self):
        from openedx.core.djangoapps.appsembler.sites.models import patched_clear_site_cache

        pre_save.connect(patched_clear_site_cache, sender='site_configuration.SiteConfiguration')
