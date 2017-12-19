
import logging
from django.apps import AppConfig
from .microsite import enable_microsites

log = logging.getLogger(__name__)


class MicrositeConfigurationConfig(AppConfig):
    name = 'microsite_configuration'
    verbose_name = "Microsite Configuration"

    def ready(self):
        # Mako requires the directories to be added after the django setup.
        enable_microsites(log)
