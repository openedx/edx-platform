"""
Script for cloning a course
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.store_utilities import clone_course
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from student.roles import CourseInstructorRole, CourseStaffRole
from xmodule.modulestore.keys import CourseKey


#
# To run from command line: ./manage.py cms clone_course --settings=dev master/300/cough edx/111/foo
#
class Command(BaseCommand):
    """Clone a MongoDB-backed course to another location"""
    help = 'Clone a MongoDB backed course to another location'

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) != 2:
            raise CommandError("clone requires 2 arguments: <source-course_id> <dest-course_id>")

        source_course_id = CourseKey.from_string(args[0])
        dest_course_id = CourseKey.from_string(args[1])

        mstore = modulestore('direct')
        cstore = contentstore()

        mstore.ignore_write_events_on_courses.add(dest_course_id)

        print("Cloning course {0} to {1}".format(source_course_id, dest_course_id))

        if clone_course(mstore, cstore, source_course_id, dest_course_id):
            print("copying User permissions...")
            # purposely avoids auth.add_user b/c it doesn't have a caller to authorize
            CourseInstructorRole(dest_course_id).add_users(
                *CourseInstructorRole(source_course_id).users_with_role()
            )
            CourseStaffRole(dest_course_id).add_users(
                *CourseStaffRole(source_course_id).users_with_role()
            )
