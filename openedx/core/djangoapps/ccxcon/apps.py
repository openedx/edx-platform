"""
Configuration for CCX connector
"""


from django.apps import AppConfig


class CCXConnectorConfig(AppConfig):
    name = 'openedx.core.djangoapps.ccxcon'
    verbose_name = "CCX Connector"

    def ready(self):
        from . import signals
