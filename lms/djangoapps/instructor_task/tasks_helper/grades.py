"""
Functionality for generating grade reports.
"""
import logging
import re
from collections import OrderedDict
from datetime import datetime
from itertools import chain, izip, izip_longest
from time import time

from lazy import lazy
from pytz import UTC

from certificates.models import CertificateWhitelist, GeneratedCertificate, certificate_info_for_user
from courseware.courses import get_course_by_id
from instructor_analytics.basic import list_problem_responses
from instructor_analytics.csvs import format_dictlist
from lms.djangoapps.grades.context import grading_context, grading_context_for_course
from lms.djangoapps.grades.models import PersistentCourseGrade
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.teams.models import CourseTeamMembership
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.content.block_structure.api import get_course_in_cache
from openedx.core.djangoapps.course_groups.cohorts import bulk_cache_cohorts, get_cohort, is_course_cohorted
from openedx.core.djangoapps.user_api.course_tag.api import BulkCourseTags
from student.models import CourseEnrollment
from student.roles import BulkRoleCache
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
        grading_cxt = grading_context(self.course, self.course_structure)
        graded_assignments_map = OrderedDict()
        for assignment_type_name, subsection_infos in grading_cxt['all_graded_subsections_by_type'].iteritems():
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
        self.verified_users = [
            verified.user.id for verified in
            SoftwareSecurePhotoVerification.verified_query().filter(user__in=users).select_related('user')
        ]


class _CourseGradeBulkContext(object):
    def __init__(self, context, users):
        self.certs = _CertificateBulkContext(context, users)
        self.teams = _TeamBulkContext(context, users)
        self.enrollments = _EnrollmentBulkContext(context, users)
        bulk_cache_cohorts(context.course_id, users)
        BulkRoleCache.prefetch(users)
        PersistentCourseGrade.prefetch(context.course_id, users)
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
        return (
            ["Student ID", "Email", "Username"] +
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
            users = filter(lambda u: u is not None, users)
            yield self._rows_for_users(context, users)

    def _compile(self, context, batched_rows):
        """
        Compiles and returns the complete list of (success_rows, error_rows) for
        the given batched_rows and context.
        """
        # partition and chain successes and errors
        success_rows, error_rows = izip(*batched_rows)
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
        for assignment_info in graded_assignments.itervalues():
            if assignment_info['separate_subsection_avg_headers']:
                grades_header.extend(assignment_info['subsection_headers'].itervalues())
            grades_header.append(assignment_info['average_header'])
        return grades_header

    def _batch_users(self, context):
        """
        Returns a generator of batches of users.
        """
        def grouper(iterable, chunk_size=self.USER_BATCH_SIZE, fillvalue=None):
            args = [iter(iterable)] * chunk_size
            return izip_longest(*args, fillvalue=fillvalue)

        users = CourseEnrollment.objects.users_enrolled_in(context.course_id, include_inactive=True)
        users = users.select_related('profile')
        return grouper(users)

    def _user_grades(self, course_grade, context):
        """
        Returns a list of grade results for the given course_grade corresponding
        to the headers for this report.
        """
        grade_results = []
        for assignment_type, assignment_info in context.graded_assignments.iteritems():

            subsection_grades, subsection_grades_results = self._user_subsection_grades(
                course_grade,
                assignment_info['subsection_headers'],
            )
            grade_results.extend(subsection_grades_results)

            assignment_average = self._user_assignment_average(course_grade, subsection_grades, assignment_info)
            if assignment_average is not None:
                grade_results.append([assignment_average])

        return [course_grade.percent] + _flatten(grade_results)

    def _user_subsection_grades(self, course_grade, subsection_headers):
        """
        Returns a list of grade results for the given course_grade corresponding
        to the headers for this report.
        """
        subsection_grades = []
        grade_results = []
        for subsection_location in subsection_headers:
            subsection_grade = course_grade.subsection_grade(subsection_location)
            if subsection_grade.attempted_graded:
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
        verification_status = SoftwareSecurePhotoVerification.verification_status_for_user(
            user,
            context.course_id,
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
            course_grade.letter_grade,
            is_whitelisted,
            bulk_certs.certificates_by_user.get(user.id),
        )
        TASK_LOG.info(
            u'Student certificate eligibility: %s '
            u'(user=%s, course_id=%s, grade_percent=%s letter_grade=%s gradecutoffs=%s, allow_certificate=%s, '
            u'is_whitelisted=%s)',
            certificate_info[0],
            user,
            context.course_id,
            course_grade.percent,
            course_grade.letter_grade,
            context.course.grade_cutoffs,
            user.profile.allow_certificate,
            is_whitelisted,
        )
        return certificate_info

    def _rows_for_users(self, context, users):
        """
        Returns a list of rows for the given users for this report.
        """
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
                    error_rows.append([user.id, user.username, error.message])
                else:
                    success_rows.append(
                        [user.id, user.email, user.username] +
                        self._user_grades(course_grade, context) +
                        self._user_cohort_group_names(user, context) +
                        self._user_experiment_group_names(user, context) +
                        self._user_team_names(user, bulk_context.teams) +
                        self._user_verification_mode(user, context, bulk_context.enrollments) +
                        self._user_certificate_info(user, context, course_grade, bulk_context.certs) +
                        [_user_enrollment_status(user, context.course_id)]
                    )
            return success_rows, error_rows


class ProblemGradeReport(object):
    @classmethod
    def generate(cls, _xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
        """
        Generate a CSV containing all students' problem grades within a given
        `course_id`.
        """
        start_time = time()
        start_date = datetime.now(UTC)
        status_interval = 100
        enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id, include_inactive=True)
        task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

        # This struct encapsulates both the display names of each static item in the
        # header row as values as well as the django User field names of those items
        # as the keys.  It is structured in this way to keep the values related.
        header_row = OrderedDict([('id', 'Student ID'), ('email', 'Email'), ('username', 'Username')])

        course = get_course_by_id(course_id)
        graded_scorable_blocks = cls._graded_scorable_blocks_to_header(course)

        # Just generate the static fields for now.
        rows = [list(header_row.values()) + ['Enrollment Status', 'Grade'] + _flatten(graded_scorable_blocks.values())]
        error_rows = [list(header_row.values()) + ['error_msg']]
        current_step = {'step': 'Calculating Grades'}

        # Bulk fetch and cache enrollment states so we can efficiently determine
        # whether each user is currently enrolled in the course.
        CourseEnrollment.bulk_fetch_enrollment_states(enrolled_students, course_id)

        for student, course_grade, error in CourseGradeFactory().iter(enrolled_students, course):
            student_fields = [getattr(student, field_name) for field_name in header_row]
            task_progress.attempted += 1

            if not course_grade:
                err_msg = error.message
                # There was an error grading this student.
                if not err_msg:
                    err_msg = u'Unknown error'
                error_rows.append(student_fields + [err_msg])
                task_progress.failed += 1
                continue

            enrollment_status = _user_enrollment_status(student, course_id)

            earned_possible_values = []
            for block_location in graded_scorable_blocks:
                try:
                    problem_score = course_grade.problem_scores[block_location]
                except KeyError:
                    earned_possible_values.append([u'Not Available', u'Not Available'])
                else:
                    if problem_score.first_attempted:
                        earned_possible_values.append([problem_score.earned, problem_score.possible])
                    else:
                        earned_possible_values.append([u'Not Attempted', problem_score.possible])

            rows.append(student_fields + [enrollment_status, course_grade.percent] + _flatten(earned_possible_values))

            task_progress.succeeded += 1
            if task_progress.attempted % status_interval == 0:
                task_progress.update_task_state(extra_meta=current_step)

        # Perform the upload if any students have been successfully graded
        if len(rows) > 1:
            upload_csv_to_report_store(rows, 'problem_grade_report', course_id, start_date)
        # If there are any error rows, write them out as well
        if len(error_rows) > 1:
            upload_csv_to_report_store(error_rows, 'problem_grade_report_err', course_id, start_date)

        return task_progress.update_task_state(extra_meta={'step': 'Uploading CSV'})

    @classmethod
    def _graded_scorable_blocks_to_header(cls, course):
        """
        Returns an OrderedDict that maps a scorable block's id to its
        headers in the final report.
        """
        scorable_blocks_map = OrderedDict()
        grading_context = grading_context_for_course(course)
        for assignment_type_name, subsection_infos in grading_context['all_graded_subsections_by_type'].iteritems():
            for subsection_index, subsection_info in enumerate(subsection_infos, start=1):
                for scorable_block in subsection_info['scored_descendants']:
                    header_name = (
                        u"{assignment_type} {subsection_index}: "
                        u"{subsection_name} - {scorable_block_name}"
                    ).format(
                        scorable_block_name=scorable_block.display_name,
                        assignment_type=assignment_type_name,
                        subsection_index=subsection_index,
                        subsection_name=subsection_info['subsection_block'].display_name,
                    )
                    scorable_blocks_map[scorable_block.location] = [header_name + " (Earned)",
                                                                    header_name + " (Possible)"]
        return scorable_blocks_map


class ProblemResponses(object):
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

        # Compute result table and format it
        problem_location = task_input.get('problem_location')
        student_data = list_problem_responses(course_id, problem_location)
        features = ['username', 'state']
        header, rows = format_dictlist(student_data, features)

        task_progress.attempted = task_progress.succeeded = len(rows)
        task_progress.skipped = task_progress.total - task_progress.attempted

        rows.insert(0, header)

        current_step = {'step': 'Uploading CSV'}
        task_progress.update_task_state(extra_meta=current_step)

        # Perform the upload
        problem_location = re.sub(r'[:/]', '_', problem_location)
        csv_name = 'student_state_from_{}'.format(problem_location)
        upload_csv_to_report_store(rows, csv_name, course_id, start_date)

        return task_progress.update_task_state(extra_meta=current_step)
