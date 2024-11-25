"""
Django AppConfig for Content Libraries Implementation
"""
# -*- coding: utf-8 -*-


from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs, PluginSettings

from openedx.core.djangoapps.plugins.constants import ProjectType


class ContentLibrariesConfig(AppConfig):
    """
    Django AppConfig for Content Libraries Implementation
    """

    name = 'openedx.core.djangoapps.content_libraries'
<<<<<<< HEAD
    verbose_name = 'Content Libraries (Blockstore-based)'
=======
    verbose_name = 'Content Libraries (Learning-Core-based)'
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    # This is designed as a plugin for now so that
    # the whole thing is self-contained and can easily be enabled/disabled
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.CMS: {
                # The namespace to provide to django's urls.include.
                PluginURLs.NAMESPACE: 'content_libraries',
            },
        },
        PluginSettings.CONFIG: {
            ProjectType.CMS: {
            },
        },
    }

    def ready(self):
        """
        Import signal handler's module to ensure they are registered.
        """
        from . import signal_handlers  # pylint: disable=unused-import
