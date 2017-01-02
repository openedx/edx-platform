"""
Command to add UUID for Instructor.
"""

import uuid
import logging


from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.models.course_details import CourseDetails

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        ./manage.py cms add_instructor_ids --username <username> --orgs <org1> <org2>
        --course_keys <key1> <key2> ... --settings=devstack
    """
    help = './manage.py cms add_instructor_ids --username <username> --orgs <org1> <org2> ... '\
           ' --course_keys <key1> <key2> ... --settings=devstack'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--course_keys',
            nargs='+',
            help='Enter one or more course keys',
            required=False,
            default=[]
        )

        parser.add_argument(
            '--orgs',
            nargs='+',
            help='Enter one or more organizations',
            required=False,
            default=[]
        )

        parser.add_argument(
            '--username',
            required=True,
            help='Enter an existing username',
        )

    @staticmethod
    def _populate_uuid(username, course_keys):
        """
        Populate the uuid in each instructor.
        """
        for key in course_keys:
            key_object = CourseKey.from_string(key)
            course_descriptor = CourseDetails.fetch(key_object)

            # Adding UUID in each instructor
            for instructor in course_descriptor.instructor_info.get("instructors", []):     # pylint: disable=E1101
                if "uuid" not in instructor:
                    instructor["uuid"] = str(uuid.uuid4())

            # Updating the course
            CourseDetails.update_from_json(
                key_object,
                course_descriptor.__dict__,
                User.objects.get(username=username)
            )

    def handle(self, *args, **options):

        username = options['username']
        organizations = options.get('orgs', [])
        course_keys = options.get('course_keys', [])

        if not organizations and not course_keys:
            raise CommandError('You have to provide organizations or course keys.')

        if organizations:
            # Conversion to unicode for better readability
            course_keys = [
                unicode(course_id) for course_id in CourseOverview.objects.filter(org__in=organizations).values_list(
                    'id', flat=True
                )
            ]

            for key in course_keys:
                print key

            question = "This will populate instructor UUID in all these courses. Proceed? (y/n): "
            if str(raw_input(question)).lower().strip()[0] == 'y':
                self._populate_uuid(username, course_keys)
        else:
            self._populate_uuid(username, course_keys)
