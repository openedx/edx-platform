# -*- coding: utf-8 -*-
"""
Command to automatically produce the grade reports as CSV files.
The reports and the destination location are the same as the "Generate grade report" button
which is available in the instructor dashboard.
The files must be retrieved manually from the instructor dashboard.

Note: this is a prototype, a proof of concept. Code is still ugly. When we check that the
approach works as expected, we'll work on the elegant solution to be sent upstream.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import csv
import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

import lms.djangoapps.instructor_task.api
from lms.djangoapps.instructor_task.tasks import calculate_grades_csv
from lms.djangoapps.instructor_task.api_helper import _reserve_task
from lms.djangoapps.grades.tasks import recalculate_course_and_subsection_grades_for_user
from openedx.core.lib.command_utils import get_mutually_exclusive_required_option, parse_course_keys
from xmodule.modulestore.django import modulestore

from util.db import outer_atomic

LOGGER = logging.getLogger(__name__)

# Used in v1
# class FakeRequestWithUser:
#     user = None
#     META = {}
#
#     def __init__(self, user):
#         self.user = user
#         self.META['SERVER_NAME'] = 'afakehostname'
#         self.META['HTTP_X_FORWARDED_PROTO'] = 'https'
#         self.META['REMOTE_ADDR'] = '127.0.0.1'
#
#     def is_secure(self):
#         # yes, very
#         return True
#
#     def get_host(self):
#         return "afakehostname"


class Command(BaseCommand):
    """
    Management command to launch the generation of a grade report task.
    """
    help = """
    Launch a grade report task for the chosen courses.
    It has the same effect as clicking the button in the Instructor Dashboard. The grade reports can be
    downloaded from the Instructor Dashboard.

    It's particularly useful in a cron job when there are many courses whose grades need to be exported daily.

    Example usage:
        $ ./manage.py lms generate_csv_grade_reports --requester adminstaff --courses course-v1:edX+DemoX+Demo_Course course-v1:DCL+TE1+2018-01
    """

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
        parser.add_argument(
            '--requester',
            help='Username of user that appears as requester of the grade report.',
            type=str,
            required=True,
        )

    def handle(self, *args, **options):
        user = User.objects.get(username=options['requester'])
        LOGGER.info("Launching reports from username %s", user.username)
        for course_key in self._get_course_keys(options):
            LOGGER.info("Launching report for course %s", course_key)

            # v1, works:
            # request = FakeRequestWithUser(user=user)
            # lms.djangoapps.instructor_task.api.submit_calculate_grades_csv(request, course_key)

            # v2, expanding „request“:
            # from lms.djangoapps.instructor_task.tasks import calculate_grades_csv
            # submit_task(request, 'grade_course', calculate_grades_csv, course_key, {}, "")

            # v3. expanding „request“ still more, and a lot of bad copy+paste, and some forbidden calls
            # from lms.djangoapps.instructor_task.tasks import calculate_grades_csv
            # from lms.djangoapps.instructor_task.api_helper import _reserve_task, _get_xmodule_instance_args
            # from util.db import outer_atomic
            # with outer_atomic():
            #     # check to see if task is already running, and reserve it otherwise:
            #     instructor_task = _reserve_task(course_key, 'grade_course', "", {}, user)
            # task_id = instructor_task.task_id
            # task_args = [instructor_task.id, _get_xmodule_instance_args(request, task_id)]
            # print("task_args are:", task_args)
            # try:
            #     calculate_grades_csv.apply_async(task_args, task_id=task_id)
            # 
            # except Exception as error:
            #     _handle_instructor_task_failure(instructor_task, error)

            # v4: like v3 but overwriting data to reduce calling internal methods:
            # Could be moved into api_helper, so that calling private methods be fine
            with outer_atomic():
                # check to see if task is already running, and reserve it otherwise:
                instructor_task = _reserve_task(course_key, 'grade_course', "", {}, user)
            task_id = instructor_task.task_id
            # overwriting (testing)
            task_args = [instructor_task.id, {'request_info': {}, 'task_id': task_id}]
            # print("task_args (overwritten):", task_args)
            try:
                calculate_grades_csv.apply_async(task_args, task_id=task_id)
            except Exception as error:
                _handle_instructor_task_failure(instructor_task, error)

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
