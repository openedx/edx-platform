"""
App configurations
"""

from django.apps import AppConfig


class ModulestoreMigratorConfig(AppConfig):
    """
    App for importing legacy content from the modulestore.
    """

    name = 'cms.djangoapps.modulestore_migrator'
