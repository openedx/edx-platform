from django.apps import AppConfig


class CustomSettingsConfig(AppConfig):
    name = u'custom_settings'

    def ready(self):
        """
        Connect signal handlers.
        """
        import custom_settings.signals.handlers
