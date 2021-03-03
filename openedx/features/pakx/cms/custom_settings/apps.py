"""
Custom settings app configurations
"""
from django.apps import AppConfig


class CustomSettingsConfig(AppConfig):
    name = 'openedx.features.pakx.cms.custom_settings'
    verbose_name = 'Custom settings app'

    def ready(self):
        """
        Connect signal handlers.
        """
        import openedx.features.pakx.cms.custom_settings.signals.handlers
