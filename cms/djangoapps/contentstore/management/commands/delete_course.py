"""
    Command for deleting courses

    Arguments:
        arg1 (str): Course key of the course to delete
        arg2 (str): 'commit'

    Returns:
        none
"""
from django.core.management.base import BaseCommand, CommandError
from .prompt import query_yes_no
from contentstore.utils import delete_course_and_groups
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore


class Command(BaseCommand):
    """
    Delete a MongoDB backed course
    """
    help = '''Delete a MongoDB backed course'''

    def handle(self, *args, **options):
        if len(args) == 0:
            raise CommandError("Arguments missing: 'org/number/run commit'")

        if len(args) == 1:
            if args[0] == 'commit':
                raise CommandError("Delete_course requires a course_key <org/number/run> argument.")
            else:
                raise CommandError("Delete_course requires a commit argument at the end")
        elif len(args) == 2:
            try:
                course_key = CourseKey.from_string(args[0])
            except InvalidKeyError:
                try:
                    course_key = SlashSeparatedCourseKey.from_deprecated_string(args[0])
                except InvalidKeyError:
                    raise CommandError("Invalid course_key: '%s'. Proper syntax: 'org/number/run commit' " % args[0])
            if args[1] != 'commit':
                raise CommandError("Delete_course requires a commit argument at the end")
        elif len(args) > 2:
            raise CommandError("Too many arguments! Expected <course_key> <commit>")

        if not modulestore().get_course(course_key):
            raise CommandError("Course with '%s' key not found." % args[0])

        print 'Actually going to delete the %s course from DB....' % args[0]
        if query_yes_no("Deleting course {0}. Confirm?".format(course_key), default="no"):
            if query_yes_no("Are you sure. This action cannot be undone!", default="no"):
                delete_course_and_groups(course_key, ModuleStoreEnum.UserID.mgmt_command)
                print "Deleted course {}".format(course_key)
