"""
Configuration for the openedx.core.djangoapps.appsembler.api Django app.
"""
from django.apps import AppConfig


class TahoeAPIConfig(AppConfig):
    """
    Configuration class for the Tahoe API Django app.
    """
    name = 'openedx.core.djangoapps.appsembler.api'
    label = 'tahoe_api'
