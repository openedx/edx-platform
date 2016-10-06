"""
Initialize the mako template lookup
"""
from django.apps import apps
from django.conf import settings
from . import add_lookup, clear_lookups
from path import path


def iter_app_dirs():
    """
    return an iterator of paths to all installed django apps.
    """
    for app_config in apps.get_app_configs():
        yield path(app_config.path) / u'templates'


def run():
    """
    Setup mako lookup directories.

    IMPORTANT: This method can be called multiple times during application startup. Any changes to this method
    must be safe for multiple callers during startup phase.
    """
    clear_lookups('main')

    template_locations = settings.MAKO_TEMPLATES
    for namespace, directories in template_locations.items():
        clear_lookups(namespace)
        for directory in directories:
            add_lookup(namespace, directory)
    for app_dir in iter_app_dirs():
        add_lookup('main', app_dir)
