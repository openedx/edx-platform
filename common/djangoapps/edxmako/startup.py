"""
Initialize the mako template lookup
"""
from django.conf import settings
from . import add_lookup


def run():
    """
    Setup mako lookup directories.

    IMPORTANT: This method can be called multiple times during application startup. Any changes to this method
    must be safe for multiple callers during startup phase.
    """
    template_locations = settings.MAKO_TEMPLATES
    for namespace, directories in template_locations.items():
        for directory in directories:
            add_lookup(namespace, directory)
