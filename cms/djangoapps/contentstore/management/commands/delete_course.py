###
### Script for cloning a course
###
from django.core.management.base import BaseCommand, CommandError
from .prompt import query_yes_no
from contentstore.utils import delete_course_and_groups
from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore import ModuleStoreEnum


class Command(BaseCommand):
    help = '''Delete a MongoDB backed course'''

    def handle(self, *args, **options):
        if len(args) != 1 and len(args) != 2:
            raise CommandError("delete_course requires one or more arguments: <course_id> |commit|")

        try:
            course_key = CourseKey.from_string(args[0])
        except InvalidKeyError:
            course_key = SlashSeparatedCourseKey.from_deprecated_string(args[0])

        commit = False
        if len(args) == 2:
            commit = args[1] == 'commit'

        if commit:
            print('Actually going to delete the course from DB....')

            if query_yes_no("Deleting course {0}. Confirm?".format(course_key), default="no"):
                if query_yes_no("Are you sure. This action cannot be undone!", default="no"):
                    delete_course_and_groups(course_key, ModuleStoreEnum.UserID.mgmt_command)
