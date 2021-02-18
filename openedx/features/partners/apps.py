from django.apps import AppConfig


class PartnersConfig(AppConfig):
    name = u'openedx.features.partners'

    def ready(self):
        """
        Connect handlers to Partners.
        """
        import handlers
