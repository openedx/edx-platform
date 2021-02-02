"""
Management command to generate allowlist certificates for one or more users in a given course run.
"""

import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.generation_handler import generate_allowlist_certificate_task

User = get_user_model()
log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to generate allowlist certificates for one or more users in a given course run.

    Example usage:
    ./manage.py lms cert_allowlist_generation -u edx verified -c course-v1:edX+DemoX+Demo_Course
    """

    help = """
    Generate allowlist certificates for one or more users in a given course run.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '-u', '--user',
            nargs="+",
            metavar='USER',
            dest='user',
            required=True,
            help='user or space-separated list of users for whom to generate allowlist certificates'
        )
        parser.add_argument(
            '-c', '--course-key',
            metavar='COURSE_KEY',
            dest='course_key',
            required=True,
            help="course run key"
        )

    def handle(self, *args, **options):
        # Parse the serialized course key into a CourseKey
        course_key = options['course_key']
        if not course_key:
            raise CommandError("You must specify a course-key")

        try:
            course_key = CourseKey.from_string(course_key)
        except InvalidKeyError as e:
            raise CommandError("You must specify a valid course-key") from e

        # Loop over each user, and ask that a cert be generated for them
        users_str = options['user']
        for user_identifier in users_str:
            user = _get_user_from_identifier(user_identifier)
            if user is not None:
                log.info(
                    'Calling generate_allowlist_certificate_task for {user} : {course}'.format(
                        user=user.id,
                        course=course_key
                    ))
                generate_allowlist_certificate_task(user, course_key)


def _get_user_from_identifier(identifier):
    """
    Using the string identifier, fetch the relevant user object from database
    """
    try:
        if '@' in identifier:
            user = User.objects.get(email=identifier)
        else:
            user = User.objects.get(username=identifier)
        return user
    except User.DoesNotExist:
        log.warning('User {user} could not be found'.format(user=identifier))
        return None
