"""
Helper functions for remote gradebook tasks
"""

import logging
import csv
from StringIO import StringIO
from datetime import datetime
from time import time

from pytz import UTC

from courseware.courses import get_course_by_id
from instructor_task.tasks_helper.misc import _progress_error
from instructor_task.tasks_helper.runner import TaskProgress
from instructor_task.tasks_helper.utils import upload_csv_to_report_store
from remote_gradebook.utils import get_remote_gradebook_resp, get_assignment_grade_datatable

log = logging.getLogger(__name__)


def create_datatable_csv(csv_file, datatable):
    """Creates a CSV file from the contents of a datatable."""
    writer = csv.writer(csv_file, dialect='excel', quotechar='"', quoting=csv.QUOTE_ALL)
    encoded_row = [unicode(s).encode('utf-8') for s in datatable['header']]
    writer.writerow(encoded_row)
    for datarow in datatable['data']:
        # 's' here may be an integer, float (eg score) or string (eg student name)
        encoded_row = [
            # If s is already a UTF-8 string, trying to make a unicode
            # object out of it will fail unless we pass in an encoding to
            # the constructor. But we can't do that across the board,
            # because s is often a numeric type. So just do this.
            s if isinstance(s, str) else unicode(s).encode('utf-8')
            for s in datarow
        ]
        writer.writerow(encoded_row)
    return csv_file


def post_grades_to_rgb(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    post course grades to remote grade book
    """
    start_time = time()
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    if not task_input['assignment_name']:
        return _progress_error("Error, assignment name missing", task_progress)

    current_step = {'step': 'Get course from modulestore'}
    task_progress.update_task_state(extra_meta=current_step)
    course = get_course_by_id(course_id)

    current_step = {'step': 'Load grades'}
    task_progress.update_task_state(extra_meta=current_step)
    __, data_table = get_assignment_grade_datatable(course, task_input['assignment_name'])

    task_progress.total = len(data_table["data"])
    task_progress.attempted = task_progress.succeeded = len(data_table["data"])
    task_progress.skipped = task_progress.total - task_progress.attempted

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    file_pointer = StringIO()
    create_datatable_csv(file_pointer, data_table)
    file_pointer.seek(0)
    files = {'datafile': file_pointer}

    error_message, __ = get_remote_gradebook_resp(
        task_input['email_id'],
        course,
        'post-grades',
        files=files,
    )

    if error_message:
        return _progress_error(error_message, task_progress)

    current_step = {
        'step': 'Posted to RGB'
    }
    return task_progress.update_task_state(extra_meta=current_step)


def generate_assignment_grade_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    create csv file for selected assignment
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    if not task_input['assignment_name']:
        return _progress_error("Error, assignment name missing", task_progress)

    current_step = {'step': 'Get course from modulestore'}
    task_progress.update_task_state(extra_meta=current_step)
    course = get_course_by_id(course_id)

    current_step = {'step': 'Load grades'}
    task_progress.update_task_state(extra_meta=current_step)
    __, data_table = get_assignment_grade_datatable(course, task_input['assignment_name'])

    rows = data_table["data"]
    task_progress.total = len(rows)
    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted
    rows.insert(0, data_table["header"])
    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'grades', course_id, start_date)

    current_step = {'step': 'Uploaded CSV'}
    return task_progress.update_task_state(extra_meta=current_step)
