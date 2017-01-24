"""
Verify the structure of courseware as to it's suitability for import
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.xml_importer import perform_xlint


class Command(BaseCommand):
    """Verify the structure of courseware as to it's suitability for import"""
    help = "Verify the structure of courseware as to it's suitability for import"

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) == 0:
            raise CommandError("import requires at least one argument: <data directory> [<course dir>...]")

        data_dir = args[0]
        if len(args) > 1:
            source_dirs = args[1:]
        else:
            source_dirs = None
        print("Importing.  Data_dir={data}, source_dirs={courses}".format(
            data=data_dir,
            courses=source_dirs))
        perform_xlint(data_dir, source_dirs, load_error_modules=False)
