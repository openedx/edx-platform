"""
Functionality for generating grade reports.
"""
from collections import OrderedDict
from datetime import datetime
from itertools import chain
import logging
from pytz import UTC
import re
from time import time

from instructor_analytics.basic import list_problem_responses
from instructor_analytics.csvs import format_dictlist
from certificates.models import CertificateWhitelist, certificate_info_for_user
from courseware.courses import get_course_by_id
from lms.djangoapps.grades.context import grading_context_for_course
from lms.djangoapps.grades.new.course_grade_factory import CourseGradeFactory
from lms.djangoapps.teams.models import CourseTeamMembership
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from openedx.core.djangoapps.course_groups.cohorts import get_cohort, is_course_cohorted
from student.models import CourseEnrollment
from xmodule.partitions.partitions_service import PartitionService
from xmodule.split_test_module import get_split_user_partitions

from .runner import TaskProgress
from .utils import upload_csv_to_report_store


TASK_LOG = logging.getLogger('edx.celery.task')


def generate_course_grade_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):  # pylint: disable=too-many-statements
    """
    For a given `course_id`, generate a grades CSV file for all students that
    are enrolled, and store using a `ReportStore`. Once created, the files can
    be accessed by instantiating another `ReportStore` (via
    `ReportStore.from_config()`) and calling `link_for()` on it. Writes are
    buffered, so we'll never write part of a CSV file to S3 -- i.e. any files
    that are visible in ReportStore will be complete ones.

    As we start to add more CSV downloads, it will probably be worthwhile to
    make a more general CSVDoc class instead of building out the rows like we
    do here.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    total_enrolled_students = enrolled_students.count()
    task_progress = TaskProgress(action_name, total_enrolled_students, start_time)

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    course = get_course_by_id(course_id)
    course_is_cohorted = is_course_cohorted(course.id)
    teams_enabled = course.teams_enabled
    cohorts_header = ['Cohort Name'] if course_is_cohorted else []
    teams_header = ['Team Name'] if teams_enabled else []

    experiment_partitions = get_split_user_partitions(course.user_partitions)
    group_configs_header = [u'Experiment Group ({})'.format(partition.name) for partition in experiment_partitions]

    certificate_info_header = ['Certificate Eligible', 'Certificate Delivered', 'Certificate Type']
    certificate_whitelist = CertificateWhitelist.objects.filter(course_id=course_id, whitelist=True)
    whitelisted_user_ids = [entry.user_id for entry in certificate_whitelist]

    # Loop over all our students and build our CSV lists in memory
    rows = []
    err_rows = [["id", "username", "error_msg"]]
    current_step = {'step': 'Calculating Grades'}

    student_counter = 0
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, Starting grade calculation for total students: %s',
        task_info_string,
        action_name,
        current_step,
        total_enrolled_students,
    )

    graded_assignments = _graded_assignments(course_id)
    grade_header = []
    for assignment_info in graded_assignments.itervalues():
        if assignment_info['use_subsection_headers']:
            grade_header.extend(assignment_info['subsection_headers'].itervalues())
        grade_header.append(assignment_info['average_header'])

    rows.append(
        ["Student ID", "Email", "Username", "Grade"] +
        grade_header +
        cohorts_header +
        group_configs_header +
        teams_header +
        ['Enrollment Track', 'Verification Status'] +
        certificate_info_header
    )

    for student, course_grade, err_msg in CourseGradeFactory().iter(course, enrolled_students):
        # Periodically update task status (this is a cache write)
        if task_progress.attempted % status_interval == 0:
            task_progress.update_task_state(extra_meta=current_step)
        task_progress.attempted += 1

        # Now add a log entry after each student is graded to get a sense
        # of the task's progress
        student_counter += 1
        TASK_LOG.info(
            u'%s, Task type: %s, Current step: %s, Grade calculation in-progress for students: %s/%s',
            task_info_string,
            action_name,
            current_step,
            student_counter,
            total_enrolled_students
        )

        if not course_grade:
            # An empty gradeset means we failed to grade a student.
            task_progress.failed += 1
            err_rows.append([student.id, student.username, err_msg])
            continue

        # We were able to successfully grade this student for this course.
        task_progress.succeeded += 1

        cohorts_group_name = []
        if course_is_cohorted:
            group = get_cohort(student, course_id, assign=False)
            cohorts_group_name.append(group.name if group else '')

        group_configs_group_names = []
        for partition in experiment_partitions:
            group = PartitionService(course_id).get_group(student, partition, assign=False)
            group_configs_group_names.append(group.name if group else '')

        team_name = []
        if teams_enabled:
            try:
                membership = CourseTeamMembership.objects.get(user=student, team__course_id=course_id)
                team_name.append(membership.team.name)
            except CourseTeamMembership.DoesNotExist:
                team_name.append('')

        enrollment_mode = CourseEnrollment.enrollment_mode_for_user(student, course_id)[0]
        verification_status = SoftwareSecurePhotoVerification.verification_status_for_user(
            student,
            course_id,
            enrollment_mode
        )
        certificate_info = certificate_info_for_user(
            student,
            course_id,
            course_grade.letter_grade,
            student.id in whitelisted_user_ids
        )

        TASK_LOG.info(
            u'Student certificate eligibility: %s '
            u'(user=%s, course_id=%s, grade_percent=%s letter_grade=%s gradecutoffs=%s, allow_certificate=%s, '
            u'is_whitelisted=%s)',
            certificate_info[0],
            student,
            course_id,
            course_grade.percent,
            course_grade.letter_grade,
            course.grade_cutoffs,
            student.profile.allow_certificate,
            student.id in whitelisted_user_ids
        )

        grade_results = []
        for assignment_type, assignment_info in graded_assignments.iteritems():
            for subsection_location in assignment_info['subsection_headers']:
                try:
                    subsection_grade = course_grade.graded_subsections_by_format[assignment_type][subsection_location]
                except KeyError:
                    grade_results.append([u'Not Available'])
                else:
                    if subsection_grade.graded_total.first_attempted is not None:
                        grade_results.append(
                            [subsection_grade.graded_total.earned / subsection_grade.graded_total.possible]
                        )
                    else:
                        grade_results.append([u'Not Attempted'])
            if assignment_info['use_subsection_headers']:
                assignment_average = course_grade.grader_result['grade_breakdown'].get(assignment_type, {}).get(
                    'percent'
                )
                grade_results.append([assignment_average])

        grade_results = list(chain.from_iterable(grade_results))

        rows.append(
            [student.id, student.email, student.username, course_grade.percent] +
            grade_results + cohorts_group_name + group_configs_group_names + team_name +
            [enrollment_mode] + [verification_status] + certificate_info
        )

    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, Grade calculation completed for students: %s/%s',
        task_info_string,
        action_name,
        current_step,
        student_counter,
        total_enrolled_students
    )

    # By this point, we've got the rows we're going to stuff into our CSV files.
    current_step = {'step': 'Uploading CSVs'}
    task_progress.update_task_state(extra_meta=current_step)
    TASK_LOG.info(u'%s, Task type: %s, Current step: %s', task_info_string, action_name, current_step)

    # Perform the actual upload
    upload_csv_to_report_store(rows, 'grade_report', course_id, start_date)

    # If there are any error rows (don't count the header), write them out as well
    if len(err_rows) > 1:
        upload_csv_to_report_store(err_rows, 'grade_report_err', course_id, start_date)

    # One last update before we close out...
    TASK_LOG.info(u'%s, Task type: %s, Finalizing grade task', task_info_string, action_name)
    return task_progress.update_task_state(extra_meta=current_step)


def generate_problem_grade_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    Generate a CSV containing all students' problem grades within a given
    `course_id`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    # This struct encapsulates both the display names of each static item in the
    # header row as values as well as the django User field names of those items
    # as the keys.  It is structured in this way to keep the values related.
    header_row = OrderedDict([('id', 'Student ID'), ('email', 'Email'), ('username', 'Username')])

    graded_scorable_blocks = _graded_scorable_blocks_to_header(course_id)

    # Just generate the static fields for now.
    rows = [list(header_row.values()) + ['Grade'] + list(chain.from_iterable(graded_scorable_blocks.values()))]
    error_rows = [list(header_row.values()) + ['error_msg']]
    current_step = {'step': 'Calculating Grades'}

    course = get_course_by_id(course_id)
    for student, course_grade, err_msg in CourseGradeFactory().iter(course, enrolled_students):
        student_fields = [getattr(student, field_name) for field_name in header_row]
        task_progress.attempted += 1

        if not course_grade:
            # There was an error grading this student.
            if not err_msg:
                err_msg = u'Unknown error'
            error_rows.append(student_fields + [err_msg])
            task_progress.failed += 1
            continue

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

        rows.append(student_fields + [course_grade.percent] + list(chain.from_iterable(earned_possible_values)))

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


def upload_problem_responses_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
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


def _graded_assignments(course_key):
    """
    Returns an OrderedDict that maps an assignment type to a dict of subsection-headers and average-header.
    """
    grading_context = grading_context_for_course(course_key)
    graded_assignments_map = OrderedDict()
    for assignment_type_name, subsection_infos in grading_context['all_graded_subsections_by_type'].iteritems():
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
        use_subsection_headers = len(subsection_infos) > 1
        if use_subsection_headers:
            average_header += u" (Avg)"

        graded_assignments_map[assignment_type_name] = {
            'subsection_headers': graded_subsections_map,
            'average_header': average_header,
            'use_subsection_headers': use_subsection_headers
        }
    return graded_assignments_map


def _graded_scorable_blocks_to_header(course_key):
    """
    Returns an OrderedDict that maps a scorable block's id to its
    headers in the final report.
    """
    scorable_blocks_map = OrderedDict()
    grading_context = grading_context_for_course(course_key)
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
                scorable_blocks_map[scorable_block.location] = [header_name + " (Earned)", header_name + " (Possible)"]
    return scorable_blocks_map
