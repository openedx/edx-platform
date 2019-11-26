"""
Command to automatically produce the grade reports as CSV files.
The reports and the destination location are the same as the "Generate grade report" button
which is available in the instructor dashboard.
The files must be retrieved manually.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import csv

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

import lms.djangoapps.instructor_task.api
from lms.djangoapps.grades.tasks import recalculate_course_and_subsection_grades_for_user
from openedx.core.lib.command_utils import get_mutually_exclusive_required_option, parse_course_keys
from xmodule.modulestore.django import modulestore

class Command(BaseCommand):
    """
    FIXME: write.
    Example usage:
        $ ./manage.py lms recalculate_learner_grades learner_courses_to_recalculate.csv
    """
    help = 'FIXME: add.    Recalculates a user\'s grades for a course, for every user in a csv of (user, course) pairs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--courses',
            dest='courses',
            nargs='+',
            help='List of (space separated) courses to report (each to a separate CSV).',
        )
        parser.add_argument(
            '--all_courses',
            help='Generate grade reports for all courses.',
            action='store_true',
            default=False,
        )

    def handle(self, *args, **options):
        user = User.objects.get(username='edx')  # FIXME
        for course_key in self._get_course_keys(options):
            print("Generating report", course_key)

            # FIXME implement this in a clean way, or remove the requirement of passsing a request object
            class FakeRequestWithUser:
                user = None
                META = {}
                def __init__(self, user):
                    self.user = user
                    self.META['REMOTE_ADDR'] = '127.0.0.1'

            request = FakeRequestWithUser(user=user)
            lms.djangoapps.instructor_task.api.submit_calculate_grades_csv(request, course_key)


    def _get_course_keys(self, options):
        """
        Return a list of courses that need grade reports.
        """
        courses_mode = get_mutually_exclusive_required_option(options, 'courses', 'all_courses')
        if courses_mode == 'all_courses':
            course_keys = [course.id for course in modulestore().get_course_summaries()]
        elif courses_mode == 'courses':
            course_keys = parse_course_keys(options['courses'])
        return course_keys

