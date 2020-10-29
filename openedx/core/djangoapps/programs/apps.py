"""
Programs Configuration
"""
from __future__ import absolute_import

from django.apps import AppConfig


class ProgramsConfig(AppConfig):
    """
    Default configuration for the "openedx.core.djangoapps.programs" Django application.
    """
    name = u'openedx.core.djangoapps.programs'

    def ready(self):
        from . import signals
