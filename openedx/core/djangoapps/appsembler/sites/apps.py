from django.apps import AppConfig

from django.db.models.signals import post_save
from django.contrib.sites.models import Site


class SitesConfig(AppConfig):
    name = 'openedx.core.djangoapps.appsembler.sites'
    label = 'appsembler_sites'

    def ready(self):
        from openedx.core.djangoapps.appsembler.sites import models

        post_save.connect(models.patched_clear_site_cache, sender=Site)
