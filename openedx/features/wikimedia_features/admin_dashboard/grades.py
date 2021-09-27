"""
Functionality for generating grade reports.
"""

import logging
import six
from collections import OrderedDict
from datetime import datetime
from itertools import chain
from time import time

from django.contrib.auth import get_user_model
from lazy import lazy
from opaque_keys.edx.keys import CourseKey
from pytz import UTC
from six.moves import zip_longest

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.grades.api import context as grades_context
from lms.djangoapps.instructor_task.config.waffle import (
    course_grade_report_verified_only,
    optimize_get_learners_switch_enabled,
)
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.course_groups.cohorts import is_course_cohorted
from xmodule.modulestore.django import modulestore
from xmodule.split_test_module import get_split_user_partitions

from openedx.features.course_experience.utils import get_course_outline_block_tree
from openedx.features.wikimedia_features.admin_dashboard.runner import TaskProgress
from lms.djangoapps.instructor_task.tasks_helper.utils import upload_csv_to_report_store

TASK_LOG = logging.getLogger('edx.celery.task')

class GradeReportBase:
    """
    Base class for grade reports (MultipleCourseGradeReport).
    """

    def _get_enrolled_learner_count(self, context):
        """
        Returns count of number of learner enrolled in course.
        """
        return CourseEnrollment.objects.users_enrolled_in(
            course_id=context.course_id,
            include_inactive=True,
            verified_only=context.report_for_verified_only,
        ).count()

    def log_task_info(self, context, message):
        """
        Updates the status on the celery task to the given message.
        Also logs the update.
        """
        fmt = 'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
        task_info_string = fmt.format(
            task_id=context.task_id,
            entry_id=context.entry_id,
            course_id=context.course_id,
            task_input=context.task_input
        )
        TASK_LOG.info('%s, Task type: %s, %s, %s', task_info_string, context.action_name,
                      message, context.task_progress.state)

    def _handle_empty_generator(self, generator, default):
        """
        Handle empty generator.
        Return default if the generator is emtpy, otherwise return all
        its iterations (including the first which was used for validation).
        """
        TASK_LOG.info('GradeReport: Checking generator')
        empty_generator_sentinel = object()
        first_iteration_output = next(generator, empty_generator_sentinel)
        generator_is_empty = first_iteration_output == empty_generator_sentinel

        if generator_is_empty:
            TASK_LOG.info('GradeReport: Generator is empty')
            yield default

        else:
            TASK_LOG.info('GradeReport: Generator is not empty')
            yield first_iteration_output
            yield from generator

    def _batch_users(self, context):
        """
        Returns a generator of batches of users.
        """
        def grouper(iterable, chunk_size=100, fillvalue=None):
            args = [iter(iterable)] * chunk_size
            return zip_longest(*args, fillvalue=fillvalue)

        def get_enrolled_learners_for_course(course_id, verified_only=False):
            """
            Get all the enrolled users in a course chunk by chunk.
            This generator method fetches & loads the enrolled user objects on demand which in chunk
            size defined. This method is a workaround to avoid out-of-memory errors.
            """
            self.log_additional_info_for_testing(
                context,
                'ProblemGradeReport: Starting batching of enrolled students'
            )

            filter_kwargs = {
                'courseenrollment__course_id': course_id,
            }
            if verified_only:
                filter_kwargs['courseenrollment__mode'] = CourseMode.VERIFIED

            user_ids_list = get_user_model().objects.filter(**filter_kwargs).values_list('id', flat=True).order_by('id')
            user_chunks = grouper(user_ids_list)
            for user_ids in user_chunks:
                user_ids = [user_id for user_id in user_ids if user_id is not None]
                min_id = min(user_ids)
                max_id = max(user_ids)
                users = get_user_model().objects.filter(
                    id__gte=min_id,
                    id__lte=max_id,
                    **filter_kwargs
                ).select_related('profile')

                self.log_additional_info_for_testing(context, 'ProblemGradeReport: user chunk yielded successfully')
                yield users

        course_id = context.course_id
        return get_enrolled_learners_for_course(course_id=course_id, verified_only=context.report_for_verified_only)

    def _compile(self, context, batched_rows):
        """
        Compiles and returns the complete list of (success_rows, error_rows) for
        the given batched_rows and context.
        """
        # partition and chain successes and errors
        success_rows, error_rows = zip(*batched_rows)
        success_rows = list(chain(*success_rows))
        error_rows = list(chain(*error_rows))

        # update metrics on task status
        context.task_progress.succeeded = len(success_rows)
        context.task_progress.failed = len(error_rows)
        context.task_progress.attempted = context.task_progress.succeeded + context.task_progress.failed
        context.task_progress.total = context.task_progress.attempted
        return success_rows, error_rows

    def _upload(self, context, success_rows, error_rows):
        """
        Creates and uploads a CSV for the given headers and rows.
        """
        date = datetime.now(UTC)
        upload_csv_to_report_store(success_rows, context.file_name, context.course_id, date)
        if len(error_rows) > 1:
            upload_csv_to_report_store(error_rows, context.file_name + '_err', context.course_id, date)

    def log_additional_info_for_testing(self, context, message):
        """
        Investigation logs for test problem grade report.

        TODO -- Remove as a part of PROD-1287
        """
        context.update_status(message)


class _CourseGradeReportContext:
    """
    Internal class that provides a common context to use for a single grade
    report.  When a report is parallelized across multiple processes,
    elements of this context are serialized and parsed across process
    boundaries.
    """

    def __init__(self, task_id, _entry_id, course_id, _task_input, action_name):
        self.task_id = task_id
        self.entry_id=_entry_id
        self.action_name = action_name
        self.task_input=_task_input,
        self.course_id = course_id
        self.task_progress = TaskProgress(self.action_name, total=None, start_time=time())
        self.report_for_verified_only = course_grade_report_verified_only(self.course_id)
        self.task_info_string = (
            'Task: {self.task_id}, '
            'InstructorTask ID: {self.entry_id}, '
            'Course: {self.course_id}, '
            'Input: {self.task_input}'
        )

    @lazy
    def course(self):
        return get_course_by_id(self.course_id)

    @lazy
    def course_structure(self):
        return get_course_in_cache(self.course_id)

    @lazy
    def course_experiments(self):
        return get_split_user_partitions(self.course.user_partitions)

    @lazy
    def teams_enabled(self):
        return self.course.teams_enabled

    @lazy
    def cohorts_enabled(self):
        return is_course_cohorted(self.course_id)

    @lazy
    def graded_assignments(self):
        """
        Returns an OrderedDict that maps an assignment type to a dict of
        subsection-headers and average-header.
        """
        grading_cxt = grades_context.grading_context(self.course, self.course_structure)
        graded_assignments_map = OrderedDict()
        for assignment_type_name, subsection_infos in grading_cxt['all_graded_subsections_by_type'].items():
            graded_subsections_map = OrderedDict()
            for subsection_index, subsection_info in enumerate(subsection_infos, start=1):
                subsection = subsection_info['subsection_block']
                header_name = "{assignment_type} {subsection_index}: {subsection_name}".format(
                    assignment_type=assignment_type_name,
                    subsection_index=subsection_index,
                    subsection_name=subsection.display_name,
                )
                graded_subsections_map[subsection.location] = header_name

            average_header = f"{assignment_type_name}"

            # Use separate subsection and average columns only if
            # there's more than one subsection.
            separate_subsection_avg_headers = len(subsection_infos) > 1
            if separate_subsection_avg_headers:
                average_header += " (Avg)"

            graded_assignments_map[assignment_type_name] = {
                'subsection_headers': graded_subsections_map,
                'average_header': average_header,
                'separate_subsection_avg_headers': separate_subsection_avg_headers,
                'grader': grading_cxt['subsection_type_graders'].get(assignment_type_name),
            }
        return graded_assignments_map

    def update_status(self, message):
        """
        Updates the status on the celery task to the given message.
        Also logs the update.
        """
        TASK_LOG.info('%s, Task type: %s, %s', self.task_info_string, self.action_name, message)
        return self.task_progress.update_task_state(extra_meta={'step': message})


class MultipleCourseGradeReport:
    """
    Class to encapsulate functionality related to generating Grade Reports.
    """
    # Batch size for chunking the list of enrollees in the course.
    USER_BATCH_SIZE = 100

    @classmethod
    def generate(cls, _xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
        """
        Public method to generate a grade report.
        """
        courses = course_id.split(",")
        course_key  = CourseKey.from_string(courses[0])
        task_id = _xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None
        with modulestore().bulk_operations(course_key):
            context = _CourseGradeReportContext(task_id, _entry_id, course_key, _task_input, action_name)
            return MultipleCourseGradeReport()._generate(context,courses)  # lint-amnesty, pylint: disable=protected-access

    def _generate(self, context,courses):
        """
        Internal method for generating a grade report for the given context.
        """
        context.update_status('Starting grades')
        success_headers = self._success_headers()
        error_headers = self._error_headers()
        batched_rows = self._batched_rows(context,courses)

        context.update_status('Compiling grades')
        success_rows, error_rows = self._compile(context, batched_rows)

        context.update_status('Uploading grades')
        self._upload(context, success_headers, success_rows, error_headers, error_rows)

        return context.update_status('Completed grades')

    def _success_headers(self):
        """
        Returns a list of all applicable column headers for this grade report.
        """
        return (
            ["Course", "Total Student" ,"Average Grade"]
        )

    def _error_headers(self):
        """
        Returns a list of error headers for this grade report.
        """
        return ["Course", "Student ID", "Username", "Error"]

    def _batched_rows(self, context,courses):
        """
        A generator of batches of (success_rows, error_rows) for this report.
        """
        for users in self._batch_users(context):
            users = [u for u in users if u is not None]
            yield self._rows_for_users(context, users,courses)

    def _compile(self, context, batched_rows):
        """
        Compiles and returns the complete list of (success_rows, error_rows) for
        the given batched_rows and context.
        """
        # partition and chain successes and errors
        success_rows, error_rows = zip(*batched_rows)
        success_rows = list(chain(*success_rows))
        error_rows = list(chain(*error_rows))

        # update metrics on task status
        context.task_progress.succeeded = len(success_rows)
        context.task_progress.failed = len(error_rows)
        context.task_progress.attempted = context.task_progress.succeeded + context.task_progress.failed
        context.task_progress.total = context.task_progress.attempted
        return success_rows, error_rows

    def _upload(self, context, success_headers, success_rows, error_headers, error_rows):
        """
        Creates and uploads a CSV for the given headers and rows.
        """
        date = datetime.now(UTC)
        upload_csv_to_report_store([success_headers] + success_rows, 'avarage_grade_report', context.course_id, date)
        if len(error_rows) > 0:
            error_rows = [error_headers] + error_rows
            upload_csv_to_report_store(error_rows, 'avarage_grade_report_err', context.course_id, date)

    def _batch_users(self, context):
        """
        Returns a generator of batches of users.
        """

        def grouper(iterable, chunk_size=self.USER_BATCH_SIZE, fillvalue=None):
            args = [iter(iterable)] * chunk_size
            return zip_longest(*args, fillvalue=fillvalue)

        def get_enrolled_learners_for_course(course_id, verified_only=False):
            """
            Get enrolled learners in a course.
            Arguments:
                course_id (CourseLocator): course_id to return enrollees for.
                verified_only (boolean): is a boolean when True, returns only verified enrollees.
            """
            if optimize_get_learners_switch_enabled():
                TASK_LOG.info('%s, Creating Course Grade with optimization', task_log_message)
                return users_for_course_v2(course_id, verified_only=verified_only)

            TASK_LOG.info('%s, Creating Course Grade without optimization', task_log_message)
            return users_for_course(course_id, verified_only=verified_only)

        def users_for_course(course_id, verified_only=False):
            """
            Get all the enrolled users in a course.
            This method fetches & loads the enrolled user objects at once which may cause
            out-of-memory errors in large courses. This method will be removed when
            `OPTIMIZE_GET_LEARNERS_FOR_COURSE` waffle flag is removed.
            """
            users = CourseEnrollment.objects.users_enrolled_in(
                course_id,
                include_inactive=True,
                verified_only=verified_only,
            )
            users = users.select_related('profile')
            return grouper(users)

        def users_for_course_v2(course_id, verified_only=False):
            """
            Get all the enrolled users in a course chunk by chunk.
            This generator method fetches & loads the enrolled user objects on demand which in chunk
            size defined. This method is a workaround to avoid out-of-memory errors.
            """
            filter_kwargs = {
                'courseenrollment__course_id': course_id,
            }
            if verified_only:
                filter_kwargs['courseenrollment__mode'] = CourseMode.VERIFIED

            user_ids_list = get_user_model().objects.filter(**filter_kwargs).values_list('id', flat=True).order_by('id')
            user_chunks = grouper(user_ids_list)
            for user_ids in user_chunks:
                user_ids = [user_id for user_id in user_ids if user_id is not None]
                min_id = min(user_ids)
                max_id = max(user_ids)
                users = get_user_model().objects.filter(
                    id__gte=min_id,
                    id__lte=max_id,
                    **filter_kwargs
                ).select_related('profile')
                yield users
        course_id = context.course_id
        task_log_message = f'{context.task_info_string}, Task type: {context.action_name}'
        return get_enrolled_learners_for_course(course_id=course_id, verified_only=context.report_for_verified_only)

    def _rows_for_users(self, context, users,courses):
        """
        Returns a list of rows for the given users for this report.
        """
        success_rows, error_rows = [], []
        for course in courses:
            course_key  = CourseKey.from_string(course)
            context = _CourseGradeReportContext(context.task_id, context.entry_id, course_key, context.task_input, context.action_name)
            total_students = 0
            for users in self._batch_users(context):
                users = [u for u in users if u is not None]
            with modulestore().bulk_operations(context.course_id):
                total_students = len(users)
                average_course_grade = 0
                for user, course_grade, error in CourseGradeFactory().iter(
                    users,
                    course=context.course,
                    collected_block_structure=context.course_structure,
                    course_key=context.course_id,
                ):
                    if not course_grade:
                        # An empty gradeset means we failed to grade a student.
                        error_rows.append([context.course.display_name, user.id, user.username, str(error)])
                    else:
                        average_course_grade = (average_course_grade + course_grade.percent)/total_students
            success_rows.append(
                [context.course.display_name,total_students,average_course_grade] )
        return success_rows, error_rows


class CourseProgressReport:
    """
    Class to encapsulate functionality related to generating Progress Reports.
    """
    # Batch size for chunking the list of enrollees in the course.
    USER_BATCH_SIZE = 100
    REQUEST = None
    
    @classmethod
    def generate(cls, _xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
        """
        Public method to generate a Progress report.
        """
        course_key  = CourseKey.from_string(course_id)
        task_id = _xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None
        with modulestore().bulk_operations(course_key):
            context = _CourseGradeReportContext(task_id, _entry_id, course_key, _task_input, action_name)
            return CourseProgressReport()._generate(context,course_id)  # lint-amnesty, pylint: disable=protected-access

    def _generate(self, context, course_id):
        """
        Internal method for generating a Progress report for the given context.
        """
        context.update_status('Starting progress')
        success_headers = self._success_headers(course_id)
        batched_rows = self._batched_rows(context)

        context.update_status('Compiling progress')
        success_rows = self._compile(context, batched_rows)

        context.update_status('Uploading progress')
        self._upload(context, success_headers, success_rows)

        return context.update_status('Completed progress')

    def _success_headers(self, course_id):
        """
        Returns a list of all applicable column headers for this progress report.
        """
        
        return (
            ["Student ID", "Email", "Username"] +
            self._unit_header(course_id)
        )

    def _unit_header(self, course_id):
        course_unit_header = []
        course_blocks = get_course_outline_block_tree(
        self.REQUEST, course_id, self.REQUEST.user
        )
        if 'children' in course_blocks:
            for section in course_blocks['children']:
                if 'children' in section:
                    for sub_section in section['children']:
                        if 'children' in sub_section:
                            for unit in sub_section['children']:
                                    course_unit_header.append(unit['display_name'])
        return  course_unit_header

    def _compile(self, context, batched_rows):
            """
            Compiles and returns the complete list of (success_rows) for
            the given batched_rows and context.
            """
            # partition and chain successes and errors
            success_rows = zip(*batched_rows)
            success_rows = list(chain(*success_rows))

            # update metrics on task status
            context.task_progress.succeeded = len(success_rows)
            context.task_progress.attempted = context.task_progress.succeeded
            context.task_progress.total = context.task_progress.attempted
            return success_rows

    def _upload(self, context, success_headers, success_rows):
            """
            Creates and uploads a CSV for the given headers and rows.
            """
            date = datetime.now(UTC)
            upload_csv_to_report_store([success_headers] + success_rows, 'progress_report', context.course_id, date)

    def _batched_rows(self, context):
        """
        A generator of batches of (success_rows) for this report.
        """
        for users in MultipleCourseGradeReport()._batch_users(context):
            users = [u for u in users if u is not None]
            yield self._rows_for_users(context, users)

    def _user_unit_progress(self, user, course_id_string):
        course_unit_progress = []
        course_blocks = get_course_outline_block_tree(
                    self.REQUEST, course_id_string, user
        )
        if 'children' in course_blocks:
            for section in course_blocks['children']:
                if 'children' in section:
                    for sub_section in section['children']:
                        if 'children' in sub_section:
                            for unit in sub_section['children']:
                                if 'children' in unit:
                                    complete_unit = 1.0
                                    for sub_unit in unit['children']:
                                        if 'completion' in sub_unit:
                                            complete_unit = complete_unit * sub_unit['completion']
                                    course_unit_progress.append(complete_unit)
        return  course_unit_progress      

    def _rows_for_users(self, context, users):
        """
        Returns a list of rows for the given users for this report.
        """
        with modulestore().bulk_operations(context.course_id):
            success_rows = []
            for user in users:
                course_id_string = six.text_type(context.course_id)
                success_rows.append(
                    [user.id, user.email, user.username] +
                    self._user_unit_progress(user, course_id_string)
                )
            return success_rows