"""
Instructor tasks related to enrollments.
"""


import logging
from datetime import datetime
from time import time

from django.contrib.sites.models import Site
from django.utils.translation import ugettext as _
from pytz import UTC

from lms.djangoapps.courseware.courses import get_course_by_id
from lms.djangoapps.instructor_analytics.basic import enrolled_students_features, list_may_enroll
from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from lms.djangoapps.instructor.enrollment import (
    enroll_email,
    get_email_params,
    get_user_email_language,
)
from lms.djangoapps.instructor.views.tools import get_student_from_identifier
from openedx.core.lib.celery.task_utils import emulate_http_request
from common.djangoapps.student.models import CourseEnrollment, User

from .runner import TaskProgress
from .utils import upload_csv_to_report_store

TASK_LOG = logging.getLogger('edx.celery.task')
FILTERED_OUT_ROLES = ['staff', 'instructor', 'finance_admin', 'sales_admin']


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



def enroll_user_to_course(request_info, course_id, username_or_email, site_name=None, context_vars=None):
    """
    Look up the given user, and if successful, enroll them to the specified course.

    Arguments:
        request_info (dict): Dict containing task request information
        course_id (str): The ID string of the course
        username_or_email: user's username or email string

    Returns:
        User object (or None if user in not registered,
        and whether the user is already enrolled or not

    """
    # First try to get a user object from the identifier (email)
    user = None
    user_already_enrolled = False
    language = None
    email_students = True
    auto_enroll = True
    thread_site = Site.objects.get(domain=request_info['host'])
    thread_author = User.objects.get(username=request_info['username'])

    try:
        user = get_student_from_identifier(username_or_email)
    except User.DoesNotExist:
        email = username_or_email
    else:
        email = user.email
        language = get_user_email_language(user)

    if user:
        course_enrollment = CourseEnrollment.get_enrollment(user=user, course_key=course_id)
        if course_enrollment:
            user_already_enrolled = True
            # Set the enrollment to active if its not already active
            if not course_enrollment.is_active:
                course_enrollment.update_enrollment(is_active=True)

    if not user or not user_already_enrolled:
        course = get_course_by_id(course_id, depth=0)
        try:
            with emulate_http_request(site=thread_site, user=thread_author):
                email_params = get_email_params(course=course, auto_enroll=auto_enroll, site_name=site_name)
                __ = enroll_email(
                    course_id, email, auto_enroll, email_students,
                    email_params, language=language, context_vars=context_vars, site=thread_site
                )
                if user:
                    TASK_LOG.info(
                        u'User %s enrolled successfully in course %s via CSV bulk enrollment',
                        username_or_email,
                        course_id
                    )
        except:
            TASK_LOG.exception(
                u'There was an error enrolling user %s in course %s via CSV bulk enrollment',
                username_or_email,
                course_id
            )
            return None, None

    return user, user_already_enrolled
