from django.apps import AppConfig


class OefConfig(AppConfig):
    name = u'oef'

    def ready(self):
        """
        Connect signal handlers.
        """
        import oef.handlers
