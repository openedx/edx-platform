###
### Script for cloning a course
###
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.store_utilities import delete_course
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseDescriptor
from .prompt import query_yes_no

from auth.authz import _delete_course_group

#
# To run from command line: rake cms:delete_course LOC=MITx/111/Foo1
#


class Command(BaseCommand):
    help = '''Delete a MongoDB backed course'''

    def handle(self, *args, **options):
        if len(args) != 1 and len(args) != 2:
            raise CommandError("delete_course requires one or more arguments: <location> |commit|")

        loc_str = args[0]

        commit = False
        if len(args) == 2:
            commit = args[1] == 'commit'

        if commit:
            print 'Actually going to delete the course from DB....'

        ms = modulestore('direct')
        cs = contentstore()

        if query_yes_no("Deleting course {0}. Confirm?".format(loc_str), default="no"):
            if query_yes_no("Are you sure. This action cannot be undone!", default="no"):
                loc = CourseDescriptor.id_to_location(loc_str)
                if delete_course(ms, cs, loc, commit):
                    print 'removing User permissions from course....'
                    # in the django layer, we need to remove all the user permissions groups associated with this course
                    if commit:
                        _delete_course_group(loc)
