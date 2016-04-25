"""
Command to dump grading context.
"""

import logging

from django.core.management.base import BaseCommand, CommandError
from instructor_analytics.basic import dump_grading_context
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Example usage:
        $ ./manage.py lms dump_grade_context --all --settings=devstack
        $ ./manage.py lms dump_grade_context 'edX/DemoX/Demo_Course' --settings=devstack
    """
    args = '<course_id course_id ...>'
    help = 'Dumps grading context for one or more courses.'

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument(
            '--all',
            action='store_true',
            dest='all',
            default=False,
            help='Dump grading context for all courses.',
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

        for course_key in course_keys:
            course = modulestore().get_course(course_key)
            grading_config_summary = dump_grading_context(course)
            print grading_config_summary
