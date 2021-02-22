"""
Django management command to clear the 'staticfiles' Django cache
"""


from django.core.cache import caches
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Implementation of the management command
    """

    help = 'Empties the Django caches["staticfiles"] cache.'

    def handle(self, *args, **_):
        staticfiles_cache = caches['staticfiles']
        staticfiles_cache.clear()
        print("Cache cleared.")
