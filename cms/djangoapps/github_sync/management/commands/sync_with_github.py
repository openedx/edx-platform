###
### Script for syncing CMS with defined github repos
###

from django.core.management.base import NoArgsCommand
from github_sync import sync_all_with_github


class Command(NoArgsCommand):
    help = \
'''Sync the CMS with the defined github repos'''

    def handle_noargs(self, **options):
        sync_all_with_github()
