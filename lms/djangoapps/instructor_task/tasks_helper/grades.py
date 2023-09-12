"""
Functionality for generating grade reports.
"""

import logging
from collections import OrderedDict, defaultdict
from datetime import datetime
from itertools import chain
from time import time

import re
import six
from lms.djangoapps.course_blocks.api import get_course_blocks
from django.conf import settings
from django.contrib.auth import get_user_model
from lazy import lazy
from opaque_keys.edx.keys import UsageKey
from pytz import UTC
from six import text_type
from six.moves import zip, zip_longest

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates.models import CertificateWhitelist, GeneratedCertificate, certificate_info_for_user
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.courseware.user_state_client import DjangoXBlockUserStateClient
from lms.djangoapps.grades.api import (
    CourseGradeFactory,
    context as grades_context,
    prefetch_course_and_subsection_grades,
)
from lms.djangoapps.instructor_analytics.basic import list_problem_responses
from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from lms.djangoapps.instructor_task.config.waffle import (
    course_grade_report_verified_only,
    optimize_get_learners_switch_enabled,
    problem_grade_report_verified_only,
)
from lms.djangoapps.teams.models import CourseTeamMembership
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.course_groups.cohorts import bulk_cache_cohorts, get_cohort, is_course_cohorted
from openedx.core.djangoapps.user_api.course_tag.api import BulkCourseTags
from openedx.core.lib.cache_utils import get_cache
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import BulkRoleCache
from xmodule.modulestore.django import modulestore
from xmodule.partitions.partitions_service import PartitionService
from xmodule.split_test_module import get_split_user_partitions
from .runner import TaskProgress
from .utils import upload_csv_to_report_store

TASK_LOG = logging.getLogger('edx.celery.task')

ENROLLED_IN_COURSE = 'enrolled'

NOT_ENROLLED_IN_COURSE = 'unenrolled'


def _user_enrollment_status(user, course_id):
    """
    Returns the enrollment activation status in the given course
    for the given user.
    """
    enrollment_is_active = CourseEnrollment.enrollment_mode_for_user(user, course_id)[1]
    if enrollment_is_active:
        return ENROLLED_IN_COURSE
    return NOT_ENROLLED_IN_COURSE


def _flatten(iterable):
    return list(chain.from_iterable(iterable))


class GradeReportBase(object):
    """
    Base class for grade reports (ProblemGradeReport and CourseGradeReport).
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
        fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
        task_info_string = fmt.format(
            task_id=context.task_id,
            entry_id=context.entry_id,
            course_id=context.course_id,
            task_input=context.task_input
        )
        TASK_LOG.info(u'%s, Task type: %s, %s, %s', task_info_string, context.action_name,
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
            for element in generator:
                yield element

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


class _CourseGradeReportContext(object):
    """
    Internal class that provides a common context to use for a single grade
    report.  When a report is parallelized across multiple processes,
    elements of this context are serialized and parsed across process
    boundaries.
    """

    def __init__(self, _xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
        self.task_info_string = (
            u'Task: {task_id}, '
            u'InstructorTask ID: {entry_id}, '
            u'Course: {course_id}, '
            u'Input: {task_input}'
        ).format(
            task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
            entry_id=_entry_id,
            course_id=course_id,
            task_input=_task_input,
        )
        self.action_name = action_name
        self.course_id = course_id
        self.task_progress = TaskProgress(self.action_name, total=None, start_time=time())
        self.report_for_verified_only = course_grade_report_verified_only(self.course_id)

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
        for assignment_type_name, subsection_infos in six.iteritems(grading_cxt['all_graded_subsections_by_type']):
            graded_subsections_map = OrderedDict()
            for subsection_index, subsection_info in enumerate(subsection_infos, start=1):
                subsection = subsection_info['subsection_block']
                header_name = u"{assignment_type} {subsection_index}: {subsection_name}".format(
                    assignment_type=assignment_type_name,
                    subsection_index=subsection_index,
                    subsection_name=subsection.display_name,
                )
                graded_subsections_map[subsection.location] = header_name

            average_header = u"{assignment_type}".format(assignment_type=assignment_type_name)

            # Use separate subsection and average columns only if
            # there's more than one subsection.
            separate_subsection_avg_headers = len(subsection_infos) > 1
            if separate_subsection_avg_headers:
                average_header += u" (Avg)"

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
        TASK_LOG.info(u'%s, Task type: %s, %s', self.task_info_string, self.action_name, message)
        return self.task_progress.update_task_state(extra_meta={'step': message})


class _ProblemGradeReportContext(object):
    """
    Internal class that provides a common context to use for a single problem
    grade report.  When a report is parallelized across multiple processes,
    elements of this context are serialized and parsed across process
    boundaries.
    """

    def __init__(self, _xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
        task_id = _xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None
        self.task_info_string = (
            'Task: {task_id}, '
            'InstructorTask ID: {entry_id}, '
            'Course: {course_id}, '
            'Input: {task_input}'
        ).format(
            task_id=task_id,
            entry_id=_entry_id,
            course_id=course_id,
            task_input=_task_input,
        )
        self.task_id = task_id
        self.entry_id = _entry_id
        self.task_input = _task_input
        self.action_name = action_name
        self.course_id = course_id
        self.report_for_verified_only = problem_grade_report_verified_only(self.course_id)
        self.task_progress = TaskProgress(self.action_name, total=None, start_time=time())
        self.file_name = 'problem_grade_report'

    @lazy
    def course(self):
        return get_course_by_id(self.course_id)

    @lazy
    def graded_scorable_blocks_header(self):
        """
        Returns an OrderedDict that maps a scorable block's id to its
        headers in the final report.
        """
        scorable_blocks_map = OrderedDict()
        grading_context = grades_context.grading_context_for_course(self.course)
        for assignment_type_name, subsection_infos in six.iteritems(grading_context['all_graded_subsections_by_type']):
            for subsection_index, subsection_info in enumerate(subsection_infos, start=1):
                for scorable_block in subsection_info['scored_descendants']:
                    header_name = (
                        "{assignment_type} {subsection_index}: "
                        "{subsection_name} - {scorable_block_name}"
                    ).format(
                        scorable_block_name=scorable_block.display_name,
                        assignment_type=assignment_type_name,
                        subsection_index=subsection_index,
                        subsection_name=subsection_info['subsection_block'].display_name,
                    )
                    scorable_blocks_map[scorable_block.location] = [header_name + " (Earned)",
                                                                    header_name + " (Possible)"]
        return scorable_blocks_map

    @lazy
    def course_structure(self):
        return get_course_in_cache(self.course_id)

    def update_status(self, message):
        """
        Updates the status on the celery task to the given message.
        Also logs the update.
        """
        TASK_LOG.info('%s, Task type: %s, %s', self.task_info_string, self.action_name, message)
        return self.task_progress.update_task_state(extra_meta={'step': message})


class _CertificateBulkContext(object):
    def __init__(self, context, users):
        certificate_whitelist = CertificateWhitelist.objects.filter(course_id=context.course_id, whitelist=True)
        self.whitelisted_user_ids = [entry.user_id for entry in certificate_whitelist]
        self.certificates_by_user = {
            certificate.user.id: certificate
            for certificate in
            GeneratedCertificate.objects.filter(course_id=context.course_id, user__in=users)
        }


class _TeamBulkContext(object):
    def __init__(self, context, users):
        self.enabled = context.teams_enabled
        if self.enabled:
            self.teams_by_user = {
                membership.user.id: membership.team.name
                for membership in
                CourseTeamMembership.objects.filter(team__course_id=context.course_id, user__in=users)
            }
        else:
            self.teams_by_user = {}


class _EnrollmentBulkContext(object):
    def __init__(self, context, users):
        CourseEnrollment.bulk_fetch_enrollment_states(users, context.course_id)
        self.verified_users = set(IDVerificationService.get_verified_user_ids(users))


class _CourseGradeBulkContext(object):
    def __init__(self, context, users):
        self.certs = _CertificateBulkContext(context, users)
        self.teams = _TeamBulkContext(context, users)
        self.enrollments = _EnrollmentBulkContext(context, users)
        bulk_cache_cohorts(context.course_id, users)
        BulkRoleCache.prefetch(users)
        prefetch_course_and_subsection_grades(context.course_id, users)
        BulkCourseTags.prefetch(context.course_id, users)


class CourseGradeReport(object):
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
        with modulestore().bulk_operations(course_id):
            context = _CourseGradeReportContext(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name)
            return CourseGradeReport()._generate(context)

    def _generate(self, context):
        """
        Internal method for generating a grade report for the given context.
        """
        context.update_status(u'Starting grades')
        success_headers = self._success_headers(context)
        error_headers = self._error_headers()
        batched_rows = self._batched_rows(context)

        context.update_status(u'Compiling grades')
        success_rows, error_rows = self._compile(context, batched_rows)

        context.update_status(u'Uploading grades')
        self._upload(context, success_headers, success_rows, error_headers, error_rows)

        return context.update_status(u'Completed grades')

    def _success_headers(self, context):
        """
        Returns a list of all applicable column headers for this grade report.
        """
        aux = ["Student ID", "Email", "Username"]
        
        if settings.UCHILEEDXLOGIN_TASK_RUN_ENABLE:                              
            aux = ["Student ID", "Run", "Email", "Username"]
        
        return (
            aux +
            self._grades_header(context) +
            (['Cohort Name'] if context.cohorts_enabled else []) +
            [u'Experiment Group ({})'.format(partition.name) for partition in context.course_experiments] +
            (['Team Name'] if context.teams_enabled else []) +
            ['Enrollment Track', 'Verification Status'] +
            ['Certificate Eligible', 'Certificate Delivered', 'Certificate Type'] +
            ['Enrollment Status']
        )

    def _error_headers(self):
        """
        Returns a list of error headers for this grade report.
        """
        return ["Student ID", "Username", "Error"]

    def _batched_rows(self, context):
        """
        A generator of batches of (success_rows, error_rows) for this report.
        """
        for users in self._batch_users(context):
            users = [u for u in users if u is not None]
            yield self._rows_for_users(context, users)

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
        upload_csv_to_report_store([success_headers] + success_rows, 'grade_report', context.course_id, date)
        if len(error_rows) > 0:
            error_rows = [error_headers] + error_rows
            upload_csv_to_report_store(error_rows, 'grade_report_err', context.course_id, date)

    def _grades_header(self, context):
        """
        Returns the applicable grades-related headers for this report.
        """
        graded_assignments = context.graded_assignments
        grades_header = ["Grade"]
        for assignment_info in six.itervalues(graded_assignments):
            if assignment_info['separate_subsection_avg_headers']:
                grades_header.extend(six.itervalues(assignment_info['subsection_headers']))
            grades_header.append(assignment_info['average_header'])
        return grades_header

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
                TASK_LOG.info(u'%s, Creating Course Grade with optimization', task_log_message)
                return users_for_course_v2(course_id, verified_only=verified_only)

            TASK_LOG.info(u'%s, Creating Course Grade without optimization', task_log_message)
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
        task_log_message = u'{}, Task type: {}'.format(context.task_info_string, context.action_name)
        return get_enrolled_learners_for_course(course_id=course_id, verified_only=context.report_for_verified_only)

    def _user_grades(self, course_grade, context):
        """
        Returns a list of grade results for the given course_grade corresponding
        to the headers for this report.
        """
        grade_results = []
        for _, assignment_info in six.iteritems(context.graded_assignments):
            subsection_grades, subsection_grades_results = self._user_subsection_grades(
                course_grade,
                assignment_info['subsection_headers'],
            )
            grade_results.extend(subsection_grades_results)

            assignment_average = self._user_assignment_average(course_grade, subsection_grades, assignment_info)
            if assignment_average is not None:
                grade_results.append([assignment_average])

        return [course_grade.percent, self.grade_percent_scaled(course_grade, context)] + _flatten(grade_results)

    def grade_percent_scaled(self, course_grade, context):
        grade_cutoff = min(context.course.grade_cutoffs.values())
        if course_grade.percent < grade_cutoff:
            return round(10. * (3. / grade_cutoff * course_grade.percent + 1.)) / 10.
        return round((3. / (1. - grade_cutoff) * course_grade.percent + (7. - (3. / (1. - grade_cutoff)))) * 10.) / 10.


    def _user_subsection_grades(self, course_grade, subsection_headers):
        """
        Returns a list of grade results for the given course_grade corresponding
        to the headers for this report.
        """
        subsection_grades = []
        grade_results = []
        for subsection_location in subsection_headers:
            subsection_grade = course_grade.subsection_grade(subsection_location)
            if subsection_grade.attempted_graded or subsection_grade.override:
                grade_result = subsection_grade.percent_graded
            else:
                grade_result = u'Not Attempted'
            grade_results.append([grade_result])
            subsection_grades.append(subsection_grade)
        return subsection_grades, grade_results

    def _user_assignment_average(self, course_grade, subsection_grades, assignment_info):
        if assignment_info['separate_subsection_avg_headers']:
            if assignment_info['grader']:
                if course_grade.attempted:
                    subsection_breakdown = [
                        {'percent': subsection_grade.percent_graded}
                        for subsection_grade in subsection_grades
                    ]
                    assignment_average, _ = assignment_info['grader'].total_with_drops(subsection_breakdown)
                else:
                    assignment_average = 0.0
                return assignment_average

    def _user_cohort_group_names(self, user, context):
        """
        Returns a list of names of cohort groups in which the given user
        belongs.
        """
        cohort_group_names = []
        if context.cohorts_enabled:
            group = get_cohort(user, context.course_id, assign=False, use_cached=True)
            cohort_group_names.append(group.name if group else '')
        return cohort_group_names

    def _user_experiment_group_names(self, user, context):
        """
        Returns a list of names of course experiments in which the given user
        belongs.
        """
        experiment_group_names = []
        for partition in context.course_experiments:
            group = PartitionService(context.course_id).get_group(user, partition, assign=False)
            experiment_group_names.append(group.name if group else '')
        return experiment_group_names

    def _user_team_names(self, user, bulk_teams):
        """
        Returns a list of names of teams in which the given user belongs.
        """
        team_names = []
        if bulk_teams.enabled:
            team_names = [bulk_teams.teams_by_user.get(user.id, '')]
        return team_names

    def _user_verification_mode(self, user, context, bulk_enrollments):
        """
        Returns a list of enrollment-mode and verification-status for the
        given user.
        """
        enrollment_mode = CourseEnrollment.enrollment_mode_for_user(user, context.course_id)[0]
        verification_status = IDVerificationService.verification_status_for_user(
            user,
            enrollment_mode,
            user_is_verified=user.id in bulk_enrollments.verified_users,
        )
        return [enrollment_mode, verification_status]

    def _user_certificate_info(self, user, context, course_grade, bulk_certs):
        """
        Returns the course certification information for the given user.
        """
        is_whitelisted = user.id in bulk_certs.whitelisted_user_ids
        certificate_info = certificate_info_for_user(
            user,
            context.course_id,
            course_grade.letter_grade,
            is_whitelisted,
            bulk_certs.certificates_by_user.get(user.id),
        )
        return certificate_info

    def _rows_for_users(self, context, users):
        """
        Returns a list of rows for the given users for this report.
        """
        user_runs= {}
        if settings.UCHILEEDXLOGIN_TASK_RUN_ENABLE: 
            from uchileedxlogin.models import EdxLoginUser
            edxlogin_user = EdxLoginUser.objects.all().values('user_id','run')
            for x in edxlogin_user:
                user_runs[x['user_id']] = x['run']
            
        with modulestore().bulk_operations(context.course_id):
            bulk_context = _CourseGradeBulkContext(context, users)

            success_rows, error_rows = [], []
            for user, course_grade, error in CourseGradeFactory().iter(
                users,
                course=context.course,
                collected_block_structure=context.course_structure,
                course_key=context.course_id,
            ):
                if not course_grade:
                    # An empty gradeset means we failed to grade a student.
                    error_rows.append([user.id, user.username, text_type(error)])
                else:
                    aux = [user.id, user.email, user.username]
                    ########### EOL ##########################                    
                    if settings.UCHILEEDXLOGIN_TASK_RUN_ENABLE: 
                        if user.id in user_runs:
                            aux = [user.id, user_runs[user.id], user.email, user.username] 
                        else:
                            aux = [user.id, "", user.email, user.username] 
                    ###########################################

                    success_rows.append(
                        aux +
                        self._user_grades(course_grade, context) +
                        self._user_cohort_group_names(user, context) +
                        self._user_experiment_group_names(user, context) +
                        self._user_team_names(user, bulk_context.teams) +
                        self._user_verification_mode(user, context, bulk_context.enrollments) +
                        self._user_certificate_info(user, context, course_grade, bulk_context.certs) +
                        [_user_enrollment_status(user, context.course_id)]
                    )
            return success_rows, error_rows


class ProblemGradeReport(GradeReportBase):
    """
    Class to encapsulate functionality related to generating Problem Grade Reports.
    """

    @classmethod
    def generate(cls, _xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
        """
        Public method to generate a grade report.
        """
        with modulestore().bulk_operations(course_id):
            context = _ProblemGradeReportContext(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name)
            # pylint: disable=protected-access
            return ProblemGradeReport()._generate(context)

    def _generate(self, context):
        """
        Generate a CSV containing all students' problem grades within a given
        `course_id`.
        """
        context.update_status('ProblemGradeReport - 1: Starting problem grades')
        success_headers = self._success_headers(context)
        error_headers = self._error_headers()
        batched_rows = self._batched_rows(context)

        context.update_status('ProblemGradeReport - 2: Compiling grades')
        success_rows, error_rows = self._compile(context, batched_rows)
        context.update_status('ProblemGradeReport - 3: Uploading grades')
        self._upload(context, [success_headers] + success_rows, [error_headers] + error_rows)

        return context.update_status('ProblemGradeReport - 4: Completed problem grades')

    def _problem_grades_header(self):
        """Problem Grade report header."""
        return OrderedDict([('id', 'Student ID'), ('email', 'Email'), ('username', 'Username')])

    def _success_headers(self, context):
        """
        Returns headers for all gradable blocks including fixed headers
        for report.
        Returns:
            list: combined header and scorable blocks
        """
        header_row = list(self._problem_grades_header().values()) + ['Enrollment Status', 'Grade']
        return header_row + _flatten(list(context.graded_scorable_blocks_header.values()))

    def _error_headers(self):
        """
        Returns error headers for error report.
        Returns:
            list: error headers
        """
        return list(self._problem_grades_header().values()) + ['error_msg']

    def _rows_for_users(self, context, users):
        """
        Returns a list of rows for the given users for this report.
        """
        self.log_additional_info_for_testing(context, 'ProblemGradeReport: Starting to process new user batch.')
        success_rows, error_rows = [], []
        for student, course_grade, error in CourseGradeFactory().iter(
            users,
            course=context.course,
            collected_block_structure=context.course_structure,
            course_key=context.course_id,
        ):
            context.task_progress.attempted += 1
            if not course_grade:
                err_msg = text_type(error)
                # There was an error grading this student.
                if not err_msg:
                    err_msg = 'Unknown error'
                error_rows.append(
                    [student.id, student.email, student.username] +
                    [err_msg]
                )
                context.task_progress.failed += 1
                continue

            earned_possible_values = []
            for block_location in context.graded_scorable_blocks_header:
                try:
                    problem_score = course_grade.problem_scores[block_location]
                except KeyError:
                    earned_possible_values.append(['Not Available', 'Not Available'])
                else:
                    if problem_score.first_attempted:
                        earned_possible_values.append([problem_score.earned, problem_score.possible])
                    else:
                        earned_possible_values.append(['Not Attempted', problem_score.possible])

            context.task_progress.succeeded += 1
            enrollment_status = _user_enrollment_status(student, context.course_id)
            success_rows.append(
                [student.id, student.email, student.username] +
                [enrollment_status, course_grade.percent] +
                _flatten(earned_possible_values)
            )

        return success_rows, error_rows

    def _batched_rows(self, context):
        """
        A generator of batches of (success_rows, error_rows) for this report.
        """
        for users in self._batch_users(context):
            yield self._rows_for_users(context, users)
            # Clear the CourseEnrollment caches after each batch of users has been processed
            get_cache('get_enrollment').clear()
            get_cache(CourseEnrollment.MODE_CACHE_NAMESPACE).clear()


class ProblemResponses(object):
    """
    Class to encapsulate functionality related to generating Problem Responses Reports.
    """

    @staticmethod
    def _build_block_base_path(block):
        """
        Return the display names of the blocks that lie above the supplied block in hierarchy.

        Arguments:
            block: a single block

        Returns:
            List[str]: a list of display names of blocks starting from the root block (Course)
        """
        path = []
        while block.parent:
            block = block.get_parent()
            path.append(block.display_name)
        return list(reversed(path))

    @classmethod
    def _build_problem_list(cls, course_blocks, root, path=None):
        """
        Generate a tuple of display names, block location paths and block keys
        for all problem blocks under the ``root`` block.
        Arguments:
            course_blocks (BlockStructureBlockData): Block structure for a course.
            root (UsageKey): This block and its children will be used to generate
                the problem list
            path (List[str]): The list of display names for the parent of root block
        Yields:
            Tuple[str, List[str], UsageKey]: tuple of a block's display name, path, and
                usage key
        """
        name = course_blocks.get_xblock_field(root, 'display_name') or root.block_type
        if path is None:
            path = [name]

        yield name, path, root

        for block in course_blocks.get_children(root):
            name = course_blocks.get_xblock_field(block, 'display_name') or block.block_type
            for result in cls._build_problem_list(course_blocks, block, path + [name]):
                yield result

    @classmethod
    def _build_student_data(
        cls, user_id, course_key, usage_key_str_list, filter_types=None,
    ):
        """
        Generate a list of problem responses for all problem under the
        ``problem_location`` root.
        Arguments:
            user_id (int): The user id for the user generating the report
            course_key (CourseKey): The ``CourseKey`` for the course whose report
                is being generated
            usage_key_str_list (List[str]): The generated report will include these
                blocks and their child blocks.
            filter_types (List[str]): The report generator will only include data for
                block types in this list.
        Returns:
              Tuple[List[Dict], List[str]]: Returns a list of dictionaries
                containing the student data which will be included in the
                final csv, and the features/keys to include in that CSV.
        """
        usage_keys = [
            UsageKey.from_string(usage_key_str).map_into_course(course_key)
            for usage_key_str in usage_key_str_list
        ]
        user = get_user_model().objects.get(pk=user_id)

        student_data = []
        max_count = settings.FEATURES.get('MAX_PROBLEM_RESPONSES_COUNT')

        store = modulestore()
        user_state_client = DjangoXBlockUserStateClient()

        student_data_keys = set()

        with store.bulk_operations(course_key):
            for usage_key in usage_keys:
                if max_count is not None and max_count <= 0:
                    break
                course_blocks = get_course_blocks(user, usage_key)
                base_path = cls._build_block_base_path(store.get_item(usage_key))
                for title, path, block_key in cls._build_problem_list(course_blocks, usage_key):
                    # Chapter and sequential blocks are filtered out since they include state
                    # which isn't useful for this report.
                    if block_key.block_type in ('sequential', 'chapter'):
                        continue

                    if filter_types is not None and block_key.block_type not in filter_types:
                        continue

                    block = store.get_item(block_key)
                    generated_report_data = defaultdict(list)

                    # Blocks can implement the generate_report_data method to provide their own
                    # human-readable formatting for user state.
                    if hasattr(block, 'generate_report_data'):
                        try:
                            user_state_iterator = user_state_client.iter_all_for_block(block_key)
                            for username, state in block.generate_report_data(user_state_iterator, max_count):
                                generated_report_data[username].append(state)
                        except NotImplementedError:
                            pass

                    responses = []

                    for response in list_problem_responses(course_key, block_key, max_count):
                        response['title'] = title
                        # A human-readable location for the current block
                        response['location'] = ' > '.join(base_path + path)
                        # A machine-friendly location for the current block
                        response['block_key'] = str(block_key)
                        # A block that has a single state per user can contain multiple responses
                        # within the same state.
                        user_states = generated_report_data.get(response['username'])
                        if user_states:
                            # For each response in the block, copy over the basic data like the
                            # title, location, block_key and state, and add in the responses
                            for user_state in user_states:
                                user_response = response.copy()
                                user_response.update(user_state)
                                student_data_keys = student_data_keys.union(list(user_state.keys()))
                                responses.append(user_response)
                        else:
                            responses.append(response)

                    student_data += responses

                    if max_count is not None:
                        max_count -= len(responses)
                        if max_count <= 0:
                            break

        # Keep the keys in a useful order, starting with username, title and location,
        # then the columns returned by the xblock report generator in sorted order and
        # finally end with the more machine friendly block_key and state.
        student_data_keys_list = (
            ['username', 'title', 'location'] +
            sorted(student_data_keys) +
            ['block_key', 'state']
        )

        return student_data, student_data_keys_list

    @classmethod
    def generate(cls, _xmodule_instance_args, _entry_id, course_id, task_input, action_name):
        """
        For a given `course_id`, generate a CSV file containing
        all student answers to a given problem, and store using a `ReportStore`.
        """
        start_time = time()
        start_date = datetime.now(UTC)
        num_reports = 1
        task_progress = TaskProgress(action_name, num_reports, start_time)
        current_step = {'step': 'Calculating students answers to problem'}
        task_progress.update_task_state(extra_meta=current_step)
        problem_locations = task_input.get('problem_locations').split(',')
        problem_types_filter = task_input.get('problem_types_filter')

        filter_types = None
        if problem_types_filter:
            filter_types = problem_types_filter.split(',')

        # Compute result table and format it
        student_data, student_data_keys = cls._build_student_data(
            user_id=task_input.get('user_id'),
            course_key=course_id,
            usage_key_str_list=problem_locations,
            filter_types=filter_types,
        )

        for data in student_data:
            for key in student_data_keys:
                data.setdefault(key, '')

        header, rows = format_dictlist(student_data, student_data_keys)

        task_progress.attempted = task_progress.succeeded = len(rows)
        task_progress.skipped = task_progress.total - task_progress.attempted

        rows.insert(0, header)

        current_step = {'step': 'Uploading CSV'}
        task_progress.update_task_state(extra_meta=current_step)

        # Perform the upload
        csv_name = cls._generate_upload_file_name(problem_locations, filter_types)
        report_name = upload_csv_to_report_store(rows, csv_name, course_id, start_date)
        current_step = {
            'step': 'CSV uploaded',
            'report_name': report_name,
        }

        return task_progress.update_task_state(extra_meta=current_step)

    @staticmethod
    def _generate_upload_file_name(problem_locations, filters):
        """Generate a concise file name based on the report generation parameters."""
        multiple_problems = len(problem_locations) > 1
        csv_name = 'student_state'
        if multiple_problems:
            csv_name += '_from_multiple_blocks'
        else:
            problem_location = re.sub(r'[:/]', '_', problem_locations[0])
            csv_name += '_from_' + problem_location
        if filters:
            csv_name += '_for_' + ','.join(filters)
        return csv_name
