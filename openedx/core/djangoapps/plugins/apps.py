"""
Plugins Application Configuration

Signal handlers are connected here.
"""

from django.apps import AppConfig


class PluginsConfig(AppConfig):
    """
    Application Configuration for Plugins.
    """
    name = u'openedx.core.djangoapps.plugins'

    plugin_app = {}

    def ready(self):
        """
        Connect plugin receivers to their signals.
        """
        from openedx.core.djangoapps.plugins import constants, plugin_signals
        from django.conf import settings

        if settings.ROOT_URLCONF == 'lms.urls':
            project_type = constants.ProjectType.LMS
        else:
            project_type = constants.ProjectType.CMS

        plugin_signals.connect_receivers(project_type)
