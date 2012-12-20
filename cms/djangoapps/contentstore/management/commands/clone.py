###
### Script for cloning a course
###
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.store_utilities import clone_course
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.modulestore import Location
from xmodule.course_module import CourseDescriptor

#
# To run from command line: rake cms:clone SOURCE_LOC=MITx/111/Foo1 DEST_LOC=MITx/135/Foo3
#

class Command(BaseCommand):
    help = \
'''Clone a MongoDB backed course to another location'''

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("clone requires two arguments: <source-location> <dest-location>")

        source_location_str = args[0]
        dest_location_str = args[1]

        print "Cloning course {0} to {1}".format(source_location_str, dest_location_str)

        source_location = CourseDescriptor.id_to_location(source_location_str)
        dest_location = CourseDescriptor.id_to_location(dest_location_str)

        clone_course(modulestore('direct'), contentstore(), source_location, dest_location)
