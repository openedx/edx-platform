###
### Script for cloning a course
###
from django.core.management.base import BaseCommand, CommandError
from xmodule.contentstore.utils import restore_asset_from_trashcan
from xmodule.modulestore import Location


class Command(BaseCommand):
    help = '''Restore a deleted asset from the trashcan back to it's original course'''

    def handle(self, *args, **options):
        if len(args) != 1 and len(args) != 0:
            raise CommandError("restore_asset_from_trashcan requires one argument: <location>")

        restore_asset_from_trashcan(args[0])

