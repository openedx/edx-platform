"""
Management command for enrolling a user into a course via the enrollment api
"""
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from enrollment.data import CourseEnrollmentExistsError
from enrollment.api import add_enrollment


class Command(BaseCommand):
    """
    Enroll a user into a course
    """
    help = """
    This enrolls a user into a given course with the default mode (e.g., 'honor', 'audit', etc).

    User email and course ID are required.

    example:
        # Enroll a user test@example.com into the demo course
        manage.py ... enroll_user_in_course -e test@example.com -c edX/Open_DemoX/edx_demo_course

        This command can be run multiple times on the same user+course (i.e. it is idempotent).
    """

    def add_arguments(self, parser):

        parser.add_argument(
            '-e', '--email',
            nargs=1,
            required=True,
            help='Email for user'
        )
        parser.add_argument(
            '-c', '--course',
            nargs=1,
            required=True,
            help='course ID to enroll the user in')

    def handle(self, *args, **options):
        """
        Get and enroll a user in the given course. Mode is optional and defers to the enrollment API for defaults.
        """
        email = options['email'][0]
        course = options['course'][0]

        user = User.objects.get(email=email)
        try:
            add_enrollment(user.username, course)
        except CourseEnrollmentExistsError:
            # If the user is already enrolled in the course, do nothing.
            pass
