"""
Commerce Application Configuration
"""
from __future__ import absolute_import

from django.apps import AppConfig


class CommerceConfig(AppConfig):
    """
    Application Configuration for Commerce.
    """
    name = 'lms.djangoapps.commerce'

    def ready(self):
        """
        Connect handlers to signals.
        """
        from . import signals  # pylint: disable=unused-variable
