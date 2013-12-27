"""
Script for cloning a course
"""
from django.core.management.base import BaseCommand, CommandError
from xmodule.modulestore.store_utilities import clone_course
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.course_module import CourseDescriptor
from student.roles import CourseInstructorRole, CourseStaffRole


#
# To run from command line: rake cms:clone SOURCE_LOC=edX/111/Foo1 DEST_LOC=edX/135/Foo3
#
class Command(BaseCommand):
    """Clone a MongoDB-backed course to another location"""
    help = 'Clone a MongoDB backed course to another location'

    def handle(self, *args, **options):
        "Execute the command"
        if len(args) != 2:
            raise CommandError("clone requires 2 arguments: <source-course_id> <dest-course_id>")

        source_course_id = args[0]
        dest_course_id = args[1]

        mstore = modulestore('direct')
        cstore = contentstore()

        org, course_num, _ = dest_course_id.split("/")
        mstore.ignore_write_events_on_courses.append('{0}/{1}'.format(org, course_num))

        print("Cloning course {0} to {1}".format(source_course_id, dest_course_id))

        source_location = CourseDescriptor.id_to_location(source_course_id)
        dest_location = CourseDescriptor.id_to_location(dest_course_id)

        if clone_course(mstore, cstore, source_location, dest_location):
            # be sure to recompute metadata inheritance after all those updates
            mstore.refresh_cached_metadata_inheritance_tree(dest_location)

            print("copying User permissions...")
            # purposely avoids auth.add_user b/c it doesn't have a caller to authorize
            CourseInstructorRole(dest_location).add_users(
                *CourseInstructorRole(source_location).users_with_role()
            )
            CourseStaffRole(dest_location).add_users(
                *CourseStaffRole(source_location).users_with_role()
            )
