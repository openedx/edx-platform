"""
Configuration for the edxmako Django application.
"""
from django.apps import AppConfig
from django.conf import settings
from . import add_lookup, clear_lookups


class EdxMakoConfig(AppConfig):
    """
    Configuration class for the edxmako Django application.
    """
    name = 'edxmako'
    verbose_name = "edX Mako Templating"

    def ready(self):
        """
        Setup mako lookup directories.

        IMPORTANT: This method can be called multiple times during application startup. Any changes to this method
        must be safe for multiple callers during startup phase.
        """
        template_locations = settings.MAKO_TEMPLATES
        for namespace, directories in template_locations.items():
            clear_lookups(namespace)
            for directory in directories:
                add_lookup(namespace, directory)
