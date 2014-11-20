"""
Script for deleting orphaned (or not-orphaned!) course references
Note: This script should be run AFTER the corresponding CMS script,
because the CMS script performs the actual modulestore removal.
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from util.prompt import query_yes_no
from util.signals import course_deleted


class Command(BaseCommand):
    """
    Command class for course reference removal
    """
    help = '''Deletes database records having reference to the specified course'''

    def handle(self, *args, **options):
        """
        This handler operation does the actual work!
        """
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
            print('Actually going to delete the course references from LMS database....')
            print('Note: There is a corresponding CMS command you must run BEFORE this command.')

            if hasattr(settings, 'TEST_ROOT'):
                course_deleted.send(sender=None, course_key=course_key)
            else:

                if query_yes_no("Deleting ALL records with references to course {0}. Confirm?".format(course_key), default="no"):
                    if query_yes_no("Are you sure. This action cannot be undone!", default="no"):

                        # Broadcast the deletion event to CMS listeners
                        print 'Notifying LMS system components...'
                        course_deleted.send(sender=None, course_key=course_key)

                        print 'LMS Course Cleanup Complete!'
