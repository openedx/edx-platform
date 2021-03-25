from django.apps import AppConfig


class PakxOverrides(AppConfig):
    name = 'openedx.features.pakx.lms.overrides'
    verbose_name = 'PakistanX overrides app'

    def ready(self):
        """
        Connect signal handlers.
        """
        import openedx.features.pakx.lms.overrides.signals.handlers
