###
### One-off script for importing courseware form XML format
###

from django.core.management.base import BaseCommand, CommandError
from contentstore import import_from_xml

unnamed_modules = 0


class Command(BaseCommand):
    help = \
'''Import the specified data directory into the default ModuleStore'''

    def handle(self, *args, **options):
        if len(args) != 3:
            raise CommandError("import requires 3 arguments: <org> <course> <data directory>")

        org, course, data_dir = args
        import_from_xml(org, course, data_dir)
