###
### Script for importing courseware from XML format
###

from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore.django import modulestore


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
        print "Importing.  Data_dir={data}, course_dirs={courses}".format(
            data=data_dir,
            courses=course_dirs)
        import_from_xml(modulestore('direct'), data_dir, course_dirs, load_error_modules=False)
