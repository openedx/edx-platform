###
### Script for importing courseware from XML format
###

from django.core.management.base import NoArgsCommand
from django.core.cache import get_cache


class Command(NoArgsCommand):
    help = 'Import the specified data directory into the default ModuleStore'

    def handle_noargs(self, **options):
        staticfiles_cache = get_cache('staticfiles')
        staticfiles_cache.clear()
