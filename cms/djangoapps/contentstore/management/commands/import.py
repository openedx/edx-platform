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
        if len(args) == 0:
            raise CommandError("import requires at least one argument: <data directory> [<course dir>...]")

        data_dir = args[0]
        if len(args) > 1:
            course_dirs = args[1:]
        else:
            course_dirs = None
        import_from_xml(data_dir, course_dirs)
