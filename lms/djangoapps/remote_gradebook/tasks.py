"""
Remote gradebook tasks
"""

import logging
import hashlib
from functools import partial

from celery import task
from django.conf import settings
from django.utils.translation import ugettext_noop

from instructor_task.api_helper import submit_task
from instructor_task.tasks_base import BaseInstructorTask
from instructor_task.tasks_helper.runner import run_main_task
from remote_gradebook.task_helpers import generate_assignment_grade_csv, post_grades_to_rgb
from remote_gradebook.constants import (
    TASK_TYPE_RGB_EXPORT_ASSIGNMENT_GRADES,
    TASK_TYPE_RGB_EXPORT_GRADES,
)

TASK_LOG = logging.getLogger('edx.celery.task')


def run_rgb_grade_export(request, course_key, assignment_name, email):
    """
    Submits a task to export assignment grades to a remote gradebook.
    """
    task_type = TASK_TYPE_RGB_EXPORT_GRADES
    task_class = export_grades_to_rgb_task
    task_input = {
        "assignment_name": assignment_name,
        "email_id": email
    }
    task_key = hashlib.md5(assignment_name).hexdigest()
    TASK_LOG.debug("Submitting task to export grades to RGB")
    return submit_task(request, task_type, task_class, course_key, task_input, task_key)


def run_assignment_grades_csv_export(request, course_key, assignment_name):
    """
    Submits a task to generate a CSV grade report for an assignment.
    """
    task_type = TASK_TYPE_RGB_EXPORT_ASSIGNMENT_GRADES
    task_class = export_assignment_grades_csv_task
    task_input = {
        "assignment_name": assignment_name
    }
    task_key = hashlib.md5(assignment_name).hexdigest()
    TASK_LOG.debug("Submitting task to export assignment grades to csv")
    return submit_task(request, task_type, task_class, course_key, task_input, task_key)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)
def export_assignment_grades_csv_task(entry_id, xmodule_instance_args):
    """
    Generate a CSV of remote grade book grades.
    """
    action_name = ugettext_noop('export_assignment_grades_csv_task')
    TASK_LOG.info("Running task to export grades to RGB")
    task_fn = partial(generate_assignment_grade_csv, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)
def export_grades_to_rgb_task(entry_id, xmodule_instance_args):
    """
    Upload grades to remote grade book (RGB).
    """
    action_name = ugettext_noop('export_grades_to_rgb_task')
    TASK_LOG.info("Running task to export assignment grades to csv")
    task_fn = partial(post_grades_to_rgb, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)
