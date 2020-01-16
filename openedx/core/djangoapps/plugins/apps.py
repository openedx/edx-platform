"""
Plugins Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig
from django.conf import settings
from . import constants, plugin_signals


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
        if settings.ROOT_URLCONF == 'lms.urls':
            project_type = constants.ProjectType.LMS
        else:
            project_type = constants.ProjectType.CMS

        plugin_signals.connect_receivers(project_type)
