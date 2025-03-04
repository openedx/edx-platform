"""
Configuration for the edxmako Django application.
"""


from django.apps import AppConfig
from django.conf import settings

from cms.djangoapps.contentstore.management.commands.edit_course_tabs import print_course
from . import add_lookup, clear_lookups


class EdxMakoConfig(AppConfig):
    """
    Configuration class for the edxmako Django application.
    """
    name = 'common.djangoapps.edxmako'
    verbose_name = "edX Mako Templating"

    def ready(self):
        """
        Setup mako lookup directories.

        IMPORTANT: This method can be called multiple times during application startup. Any changes to this method
        must be safe for multiple callers during startup phase.
        """
        for backend in settings.TEMPLATES:
            print("&&&&&&&&&((((-))))")
            print(backend)
            if 'edxmako' not in backend['BACKEND']:
                continue
            print(backend['OPTIONS'])
            namespace = backend['OPTIONS'].get('namespace', 'main')
            print(namespace)
            directories = backend['DIRS']
            print(directories)
            clear_lookups(namespace)
            for directory in directories:
                add_lookup(namespace, directory)
