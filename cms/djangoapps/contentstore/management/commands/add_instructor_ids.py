"""
Command created to back-populate a UUID on instructor data added to courses via Studio.
"""
import uuid

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.models.course_details import CourseDetails
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


class Command(BaseCommand):
    """
    Example usage:
        ./manage.py cms add_instructor_ids --username <username> --orgs <org1> <org2> ...
        --course_keys <key1> <key2> ... --settings=devstack
    """
    help = './manage.py cms add_instructor_ids --username <username> --orgs <org1> <org2> ... '\
           '--course_keys <key1> <key2> ... --settings=devstack'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--username',
            required=True,
            help='Enter an existing username',
        )

        parser.add_argument(
            '--orgs',
            nargs='+',
            help='Enter one or more organizations space separated',
            required=False,
            default=[]
        )

        parser.add_argument(
            '--course_keys',
            nargs='+',
            help='Enter one or more course keys space separated',
            required=False,
            default=[]
        )

    @staticmethod
    def _populate_instructor_uuid(course_keys, username):
        """
        Populate the uuid in each instructor.
        """
        for key in course_keys:
            key_object = CourseKey.from_string(key)
            course_descriptor = CourseDetails.fetch(key_object)
            updated = False

            # Adding UUID in each instructor
            for instructor in course_descriptor.instructor_info.get("instructors", []):     # pylint: disable=E1101
                if "uuid" not in instructor:
                    instructor["uuid"] = str(uuid.uuid4())
                    updated = True

            if updated:
                # Updating the course
                CourseDetails.update_from_json(
                    key_object,
                    course_descriptor.__dict__,
                    User.objects.get(username=username)
                )

    def handle(self, *args, **options):
        username = options.get('username')
        organizations = options.get('orgs', [])
        course_keys = options.get('course_keys', [])

        if not organizations and not course_keys:
            raise CommandError('You must provide at least one organization or course key.')

        if organizations:
            # Conversion to unicode for better readability
            course_keys = [
                unicode(course_id) for course_id in CourseOverview.objects.filter(org__in=organizations).values_list(
                    'id', flat=True
                )
            ]

            for key in course_keys:
                self.stdout.write(key)

            question = "Populate instructor UUID in the courses listed about that contain instructor data? (y/n): "
            if str(raw_input(question)).lower().strip()[0] == 'y':
                self._populate_instructor_uuid(course_keys, username)
        else:
            self._populate_instructor_uuid(course_keys, username)
