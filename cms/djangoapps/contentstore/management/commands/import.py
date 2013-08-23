"""
Script for importing courseware from XML format
"""

from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore


class Command(BaseCommand):
    """
    Import the specified data directory into the default ModuleStore
    """
    help = 'Import the specified data directory into the default ModuleStore'

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) == 0:
            raise CommandError("import requires at least one argument: <data directory> [<course dir>...]")

        data_dir = args[0]
        if len(args) > 1:
            course_dirs = args[1:]
        else:
            course_dirs = None
        print("Importing.  Data_dir={data}, course_dirs={courses}".format(
            data=data_dir,
            courses=course_dirs))
        import_from_xml(modulestore('direct'), data_dir, course_dirs, load_error_modules=False,
                        static_content_store=contentstore(), verbose=True)
