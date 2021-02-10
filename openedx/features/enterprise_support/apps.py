"""
Configuration for enterprise_support
"""


from django.apps import AppConfig


class EnterpriseSupportConfig(AppConfig):
    """
    Configuration class for enterprise_support
    """
    name = 'openedx.features.enterprise_support'

    def ready(self):
        pass
