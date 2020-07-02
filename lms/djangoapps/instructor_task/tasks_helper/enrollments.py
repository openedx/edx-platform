"""
Instructor tasks related to enrollments.
"""


import logging
from datetime import datetime
from time import time

from django.conf import settings
from django.utils.translation import ugettext as _
from pytz import UTC
from six import StringIO

from edxmako.shortcuts import render_to_string
from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.instructor.paidcourse_enrollment_report import PaidCourseEnrollmentReportProvider
from lms.djangoapps.instructor_analytics.basic import enrolled_students_features, list_may_enroll
from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from lms.djangoapps.instructor_task.models import ReportStore
from student.models import CourseAccessRole, CourseEnrollment
from util.file import course_filename_prefix_generator

from .runner import TaskProgress
from .utils import tracker_emit, upload_csv_to_report_store

TASK_LOG = logging.getLogger('edx.celery.task')
FILTERED_OUT_ROLES = ['staff', 'instructor', 'finance_admin', 'sales_admin']


def upload_enrollment_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing profile
    information for all students that are enrolled, and store using a
    `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    students_in_course = CourseEnrollment.objects.enrolled_and_dropped_out_users(course_id)
    task_progress = TaskProgress(action_name, students_in_course.count(), start_time)

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    # Loop over all our students and build our CSV lists in memory
    rows = []
    header = None
    current_step = {'step': 'Gathering Profile Information'}
    enrollment_report_provider = PaidCourseEnrollmentReportProvider()
    total_students = students_in_course.count()
    student_counter = 0
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, generating detailed enrollment report for total students: %s',
        task_info_string,
        action_name,
        current_step,
        total_students
    )

    for student in students_in_course:
        # Periodically update task status (this is a cache write)
        if task_progress.attempted % status_interval == 0:
            task_progress.update_task_state(extra_meta=current_step)
        task_progress.attempted += 1

        # Now add a log entry after certain intervals to get a hint that task is in progress
        student_counter += 1
        if student_counter % 100 == 0:
            TASK_LOG.info(
                u'%s, Task type: %s, Current step: %s, gathering enrollment profile for students in progress: %s/%s',
                task_info_string,
                action_name,
                current_step,
                student_counter,
                total_students
            )

        user_data = enrollment_report_provider.get_user_profile(student.id)
        course_enrollment_data = enrollment_report_provider.get_enrollment_info(student, course_id)
        payment_data = enrollment_report_provider.get_payment_info(student, course_id)

        # display name map for the column headers
        enrollment_report_headers = {
            'User ID': _('User ID'),
            'Username': _('Username'),
            'Full Name': _('Full Name'),
            'First Name': _('First Name'),
            'Last Name': _('Last Name'),
            'Company Name': _('Company Name'),
            'Title': _('Title'),
            'Language': _('Language'),
            'Year of Birth': _('Year of Birth'),
            'Gender': _('Gender'),
            'Level of Education': _('Level of Education'),
            'Mailing Address': _('Mailing Address'),
            'Goals': _('Goals'),
            'City': _('City'),
            'Country': _('Country'),
            'Enrollment Date': _('Enrollment Date'),
            'Currently Enrolled': _('Currently Enrolled'),
            'Enrollment Source': _('Enrollment Source'),
            'Manual (Un)Enrollment Reason': _('Manual (Un)Enrollment Reason'),
            'Enrollment Role': _('Enrollment Role'),
            'List Price': _('List Price'),
            'Payment Amount': _('Payment Amount'),
            'Coupon Codes Used': _('Coupon Codes Used'),
            'Registration Code Used': _('Registration Code Used'),
            'Payment Status': _('Payment Status'),
            'Transaction Reference Number': _('Transaction Reference Number')
        }

        if not header:
            header = list(user_data.keys()) + list(course_enrollment_data.keys()) + list(payment_data.keys())
            display_headers = []
            for header_element in header:
                # translate header into a localizable display string
                display_headers.append(enrollment_report_headers.get(header_element, header_element))
            rows.append(display_headers)

        rows.append(list(user_data.values()) + list(course_enrollment_data.values()) + list(payment_data.values()))
        task_progress.succeeded += 1

    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, Detailed enrollment report generated for students: %s/%s',
        task_info_string,
        action_name,
        current_step,
        student_counter,
        total_students
    )

    # By this point, we've got the rows we're going to stuff into our CSV files.
    current_step = {'step': 'Uploading CSVs'}
    task_progress.update_task_state(extra_meta=current_step)
    TASK_LOG.info(u'%s, Task type: %s, Current step: %s', task_info_string, action_name, current_step)

    # Perform the actual upload
    upload_csv_to_report_store(rows, 'enrollment_report', course_id, start_date, config_name='FINANCIAL_REPORTS')

    # One last update before we close out...
    TASK_LOG.info(u'%s, Task type: %s, Finalizing detailed enrollment task', task_info_string, action_name)
    return task_progress.update_task_state(extra_meta=current_step)


def upload_may_enroll_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    information about students who may enroll but have not done so
    yet, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about students who may enroll'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = task_input.get('features')
    student_data = list_may_enroll(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'may_enroll_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_students_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing profile
    information for all students that are enrolled, and store using a
    `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    current_step = {'step': 'Calculating Profile Info'}
    task_progress.update_task_state(extra_meta=current_step)

    # compute the student features table and format it
    query_features = task_input
    student_data = enrolled_students_features(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'student_profile_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)
