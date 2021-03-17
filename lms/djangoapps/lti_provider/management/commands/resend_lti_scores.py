"""
Management command to resend all lti scores for the requested course.
"""


import textwrap

from django.core.management import BaseCommand
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.lti_provider import tasks
from lms.djangoapps.lti_provider.models import GradedAssignment


class Command(BaseCommand):
    """
    Send all lti scores for the requested courses to the registered consumers.

    If no arguments are provided, send all scores for all courses.

    Examples:

        ./manage.py lms resend_lti_scores
        ./manage.py lms resend_lti_scores course-v1:edX+DemoX+Demo_Course course-v1:UBCx+course+2016-01

    """

    help = textwrap.dedent(__doc__)

    def add_arguments(self, parser):
        parser.add_argument('course_keys', type=CourseKey.from_string, nargs='*')

    def handle(self, *args, **options):
        if options['course_keys']:
            for course_key in options['course_keys']:
                for assignment in self._iter_course_assignments(course_key):
                    self._send_score(assignment)
        else:
            for assignment in self._iter_all_assignments():
                self._send_score(assignment)

    def _send_score(self, assignment):
        """
        Send the score to the LTI consumer for a single assignment.
        """
        tasks.send_composite_outcome.delay(
            assignment.user_id,
            str(assignment.course_key),
            assignment.id,
            assignment.version_number,
        )

    def _iter_all_assignments(self):
        """
        Get all the graded assignments in the system.
        """
        return GradedAssignment.objects.all()

    def _iter_course_assignments(self, course_key):
        """
        Get all the graded assignments for the given course.
        """
        return GradedAssignment.objects.filter(course_key=course_key)
