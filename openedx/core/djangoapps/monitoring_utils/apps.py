"""
Monitoring Utilities Configuration
"""
from __future__ import absolute_import

from django.apps import AppConfig


class MonitoringUtilsConfig(AppConfig):
    """
    Default configuration for the "openedx.core.djangoapps.monitoring_utils" Django application.
    """
    name = u'openedx.core.djangoapps.monitoring_utils'

    def ready(self):
        from . import signals  # pylint: disable=unused-variable
