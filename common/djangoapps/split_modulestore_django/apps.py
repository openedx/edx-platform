"""
Define this module as a Django app
"""
from django.apps import AppConfig


class SplitModulestoreDjangoBackendAppConfig(AppConfig):
    """
    Django app that provides a backend for Split Modulestore instead of MongoDB.
    """
    name = 'common.djangoapps.split_modulestore_django'
    verbose_name = "Split Modulestore Django Backend"
