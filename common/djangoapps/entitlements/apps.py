"""  # lint-amnesty, pylint: disable=django-not-configured
Entitlements Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig


class EntitlementsConfig(AppConfig):
    """
    Application Configuration for Entitlements.
    """
    name = 'common.djangoapps.entitlements'

    def ready(self):
        """
        Connect handlers to signals.
        """
