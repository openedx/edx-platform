"""
App for importing from the modulestore tools.
"""

from django.apps import AppConfig


class ImportFromModulestoreConfig(AppConfig):
    """
    App for importing legacy content from the modulestore.
    """

    name = 'cms.djangoapps.import_from_modulestore'
