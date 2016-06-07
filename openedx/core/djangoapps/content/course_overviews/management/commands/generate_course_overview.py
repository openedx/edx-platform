"""
Command to load course overviews.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms generate_course_overview --all --settings=devstack
        $ ./manage.py lms generate_course_overview 'edX/DemoX/Demo_Course' --settings=devstack
    """
    args = '<course_id course_id ...>'
    help = 'Generates and stores course overview for one or more courses.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Generate course overview for all courses.',
        )

    def handle(self, *args, **options):

        if options['all']:
            course_keys = [course.id for course in modulestore().get_course_summaries()]
        else:
            if len(args) < 1:
                raise CommandError('At least one course or --all must be specified.')
            try:
                course_keys = [CourseKey.from_string(arg) for arg in args]
            except InvalidKeyError:
                raise CommandError('Invalid key specified.')

        CourseOverview.get_select_courses(course_keys)
