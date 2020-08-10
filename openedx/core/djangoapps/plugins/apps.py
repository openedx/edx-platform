"""
Plugins Application Configuration

Signal handlers are connected here.
"""


from django.apps import AppConfig
from django.conf import settings

from edx_django_utils import plugins

from openedx.core.djangoapps.plugins.constants import ProjectType


class PluginsConfig(AppConfig):
    """
    Application Configuration for Plugins.
    """

    name = 'openedx.core.djangoapps.plugins'

    plugin_app = {}

    def ready(self):
        """
        Connect plugin receivers to their signals.
        """
        if settings.ROOT_URLCONF == 'lms.urls':
            project_type = ProjectType.LMS
        else:
            project_type = ProjectType.CMS

        plugins.connect_receivers(project_type)
