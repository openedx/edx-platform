"""
This file contains tasks that are designed to perform background operations on the
running state of a course.

"""


import logging
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from io import StringIO
from tempfile import TemporaryFile
from time import time
from zipfile import ZipFile
import csv
import os
import unicodecsv
import six

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.storage import DefaultStorage
from openassessment.data import OraAggregateData, OraDownloadData
from pytz import UTC

from lms.djangoapps.instructor_analytics.basic import get_proctored_exam_results
from lms.djangoapps.instructor_analytics.csvs import format_dictlist
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from lms.djangoapps.survey.models import SurveyAnswer
from common.djangoapps.util.file import UniversalNewlineIterator

from .runner import TaskProgress
from .utils import (
    UPDATE_STATUS_FAILED,
    UPDATE_STATUS_SUCCEEDED,
    upload_csv_to_report_store,
    upload_zip_to_report_store,
)

# define different loggers for use within tasks and on client side
TASK_LOG = logging.getLogger('edx.celery.task')


def upload_course_survey_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a html report containing the survey results for a course.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    current_step = {'step': 'Gathering course survey report information'}
    task_progress.update_task_state(extra_meta=current_step)

    distinct_survey_fields_queryset = SurveyAnswer.objects.filter(course_key=course_id).values('field_name').distinct()
    survey_fields = []
    for unique_field_row in distinct_survey_fields_queryset:
        survey_fields.append(unique_field_row['field_name'])
    survey_fields.sort()

    user_survey_answers = OrderedDict()
    survey_answers_for_course = SurveyAnswer.objects.filter(course_key=course_id).select_related('user')

    for survey_field_record in survey_answers_for_course:
        user_id = survey_field_record.user.id
        if user_id not in list(user_survey_answers.keys()):
            user_survey_answers[user_id] = {
                'username': survey_field_record.user.username,
                'email': survey_field_record.user.email
            }

        user_survey_answers[user_id][survey_field_record.field_name] = survey_field_record.field_value

    header = ["User ID", "User Name", "Email"]
    header.extend(survey_fields)
    csv_rows = []

    for user_id in user_survey_answers.keys():
        row = []
        row.append(user_id)
        row.append(user_survey_answers[user_id].get('username', ''))
        row.append(user_survey_answers[user_id].get('email', ''))
        for survey_field in survey_fields:
            row.append(user_survey_answers[user_id].get(survey_field, ''))
        csv_rows.append(row)

    task_progress.attempted = task_progress.succeeded = len(csv_rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    csv_rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(csv_rows, 'course_survey_results', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_proctored_exam_results_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    information about proctored exam results, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about proctored exam results in a course'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = [
        'course_id',
        'provider',
        'track',
        'exam_name',
        'username',
        'email',
        'attempt_code',
        'allowed_time_limit_mins',
        'is_sample_attempt',
        'started_at',
        'completed_at',
        'status',
        'review_status',
        'Suspicious Count',
        'Suspicious Comments',
        'Rules Violation Count',
        'Rules Violation Comments'
    ]

    student_data = get_proctored_exam_results(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'proctored_exam_results_report', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def _get_csv_file_content(csv_file):
    """
    returns appropriate csv file content based on input and output is
    compatible with python versions
    """
    if (not isinstance(csv_file, str)) and six.PY3:
        content = csv_file.read()
    else:
        content = csv_file

    if isinstance(content, bytes):
        csv_content = content.decode('utf-8')
    else:
        csv_content = content

    if six.PY3:
        return csv_content
    else:
        return UniversalNewlineIterator(csv_content)


def cohort_students_and_upload(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    Within a given course, cohort students in bulk, then upload the results
    using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)

    # Iterate through rows to get total assignments for task progress
    with DefaultStorage().open(task_input['file_name']) as f:
        total_assignments = 0
        if six.PY3:
            reader = csv.DictReader(_get_csv_file_content(f).splitlines())
        else:
            reader = unicodecsv.DictReader(_get_csv_file_content(f), encoding='utf-8')

        for _line in reader:
            total_assignments += 1

    task_progress = TaskProgress(action_name, total_assignments, start_time)
    current_step = {'step': 'Cohorting Students'}
    task_progress.update_task_state(extra_meta=current_step)

    # cohorts_status is a mapping from cohort_name to metadata about
    # that cohort.  The metadata will include information about users
    # successfully added to the cohort, users not found, Preassigned
    # users, and a cached reference to the corresponding cohort object
    # to prevent redundant cohort queries.
    cohorts_status = {}

    with DefaultStorage().open(task_input['file_name']) as f:

        if six.PY3:
            reader = csv.DictReader(_get_csv_file_content(f).splitlines())
        else:
            reader = unicodecsv.DictReader(_get_csv_file_content(f), encoding='utf-8')

        for row in reader:
            # Try to use the 'email' field to identify the user.  If it's not present, use 'username'.
            username_or_email = row.get('email') or row.get('username')
            cohort_name = row.get('cohort') or ''
            task_progress.attempted += 1

            if not cohorts_status.get(cohort_name):
                cohorts_status[cohort_name] = {
                    'Cohort Name': cohort_name,
                    'Learners Added': 0,
                    'Learners Not Found': set(),
                    'Invalid Email Addresses': set(),
                    'Preassigned Learners': set()
                }
                try:
                    cohorts_status[cohort_name]['cohort'] = CourseUserGroup.objects.get(
                        course_id=course_id,
                        group_type=CourseUserGroup.COHORT,
                        name=cohort_name
                    )
                    cohorts_status[cohort_name]["Exists"] = True
                except CourseUserGroup.DoesNotExist:
                    cohorts_status[cohort_name]["Exists"] = False

            if not cohorts_status[cohort_name]['Exists']:
                task_progress.failed += 1
                continue

            try:
                # If add_user_to_cohort successfully adds a user, a user object is returned.
                # If a user is preassigned to a cohort, no user object is returned (we already have the email address).
                (user, previous_cohort, preassigned) = add_user_to_cohort(cohorts_status[cohort_name]['cohort'], username_or_email)
                if preassigned:
                    cohorts_status[cohort_name]['Preassigned Learners'].add(username_or_email)
                    task_progress.preassigned += 1
                else:
                    cohorts_status[cohort_name]['Learners Added'] += 1
                    task_progress.succeeded += 1
            except User.DoesNotExist:
                # Raised when a user with the username could not be found, and the email is not valid
                cohorts_status[cohort_name]['Learners Not Found'].add(username_or_email)
                task_progress.failed += 1
            except ValidationError:
                # Raised when a user with the username could not be found, and the email is not valid,
                # but the entered string contains an "@"
                # Since there is no way to know if the entered string is an invalid username or an invalid email,
                # assume that a string with the "@" symbol in it is an attempt at entering an email
                cohorts_status[cohort_name]['Invalid Email Addresses'].add(username_or_email)
                task_progress.failed += 1
            except ValueError:
                # Raised when the user is already in the given cohort
                task_progress.skipped += 1

            task_progress.update_task_state(extra_meta=current_step)

    current_step['step'] = 'Uploading CSV'
    task_progress.update_task_state(extra_meta=current_step)

    # Filter the output of `add_users_to_cohorts` in order to upload the result.
    output_header = ['Cohort Name', 'Exists', 'Learners Added', 'Learners Not Found', 'Invalid Email Addresses', 'Preassigned Learners']
    output_rows = [
        [
            ','.join(status_dict.get(column_name, '')) if (column_name == 'Learners Not Found'
                                                           or column_name == 'Invalid Email Addresses'
                                                           or column_name == 'Preassigned Learners')
            else status_dict[column_name]
            for column_name in output_header
        ]
        for _cohort_name, status_dict in six.iteritems(cohorts_status)
    ]
    output_rows.insert(0, output_header)
    upload_csv_to_report_store(output_rows, 'cohort_results', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_ora2_data(
        _xmodule_instance_args, _entry_id, course_id, _task_input, action_name
):
    """
    Collect ora2 responses and upload them to S3 as a CSV
    """

    start_date = datetime.now(UTC)
    start_time = time()

    num_attempted = 1
    num_total = 1

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    task_progress = TaskProgress(action_name, num_total, start_time)
    task_progress.attempted = num_attempted

    curr_step = {'step': "Collecting responses"}
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s for all submissions',
        task_info_string,
        action_name,
        curr_step,
    )

    task_progress.update_task_state(extra_meta=curr_step)

    try:
        header, datarows = OraAggregateData.collect_ora2_data(course_id)
        rows = [header] + [row for row in datarows]
    # Update progress to failed regardless of error type
    except Exception:  # pylint: disable=broad-except
        TASK_LOG.exception('Failed to get ORA data.')
        task_progress.failed = 1
        curr_step = {'step': "Error while collecting data"}

        task_progress.update_task_state(extra_meta=curr_step)

        return UPDATE_STATUS_FAILED

    task_progress.succeeded = 1
    curr_step = {'step': "Uploading CSV"}
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s',
        task_info_string,
        action_name,
        curr_step,
    )
    task_progress.update_task_state(extra_meta=curr_step)

    report_name = upload_csv_to_report_store(rows, 'ORA_data', course_id, start_date)

    curr_step = {'step': 'Finalizing ORA data report','report_name': report_name}
    task_progress.update_task_state(extra_meta=curr_step)
    TASK_LOG.info(u'%s, Task type: %s, Upload complete.', task_info_string, action_name)

    return UPDATE_STATUS_SUCCEEDED


def _task_step(task_progress, task_info_string, action_name):
    """
    Returns a context manager, that logs error and updates TaskProgress
    filures counter in case inner block throws an exception.
    """

    @contextmanager
    def _step_context_manager(step_description, exception_text, step_error_description):
        curr_step = {'step': step_description}
        TASK_LOG.info(
            '%s, Task type: %s, Current step: %s',
            task_info_string,
            action_name,
            curr_step,
        )

        task_progress.update_task_state(extra_meta=curr_step)

        try:
            yield

        # Update progress to failed regardless of error type
        except Exception:  # pylint: disable=broad-except
            TASK_LOG.exception(exception_text)
            task_progress.failed = 1

            task_progress.update_task_state(extra_meta={'step': step_error_description})

    return _step_context_manager


def upload_ora2_submission_files(
    _xmodule_instance_args, _entry_id, course_id, _task_input, action_name
):
    """
    Creates zip archive with submission files in three steps:

    1. Collect all files information using ORA download helper.
    2. Download all submission attachments, put them in temporary zip
        file along with submission texts and csv downloads list.
    3. Upload zip file into reports storage.
    """

    start_time = time()
    start_date = datetime.now(UTC)

    num_attempted = 1
    num_total = 1

    fmt = 'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    task_progress = TaskProgress(action_name, num_total, start_time)
    task_progress.attempted = num_attempted

    step_manager = _task_step(task_progress, task_info_string, action_name)

    submission_files_data = None
    with step_manager(
        'Collecting attachments data',
        'Failed to get ORA submissions attachments data.',
        'Error while collecting data',
    ):
        submission_files_data = OraDownloadData.collect_ora2_submission_files(course_id)

    if submission_files_data is None:
        return UPDATE_STATUS_FAILED

    with TemporaryFile('rb+') as zip_file:
        compressed = None
        with step_manager(
            'Downloading and compressing attachments files',
            'Failed to download and compress submissions attachments.',
            'Error while downloading and compressing submissions attachments',
        ):
            compressed = OraDownloadData.create_zip_with_attachments(zip_file, course_id, submission_files_data)

        if compressed is None:
            return UPDATE_STATUS_FAILED

        zip_filename = None
        with step_manager(
            'Uploading zip file to storage',
            'Failed to upload zip file to storage.',
            'Error while uploading zip file to storage',
        ):
            zip_filename = upload_zip_to_report_store(zip_file, 'submission_files', course_id, start_date),

        if not zip_filename:
            return UPDATE_STATUS_FAILED

    task_progress.succeeded = 1
    curr_step = {'step': 'Finalizing attachments extracting'}
    task_progress.update_task_state(extra_meta=curr_step)
    TASK_LOG.info(u'%s, Task type: %s, Upload complete.', task_info_string, action_name)

    return UPDATE_STATUS_SUCCEEDED
