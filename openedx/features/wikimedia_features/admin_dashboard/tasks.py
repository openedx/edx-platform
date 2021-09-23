"""
This file contains tasks that are designed to perform background operations on the
running state of a course.

At present, these tasks all operate on StudentModule objects in one way or another,
so they share a visitor architecture.  Each task defines an "update function" that
takes a module_descriptor, a particular StudentModule object, and xmodule_instance_args.

A task may optionally specify a "filter function" that takes a query for StudentModule
objects, and adds additional filter clauses.

A task also passes through "xmodule_instance_args", that are used to provide
information to our code that instantiates xmodule instances.

The task definition then calls the traversal function, passing in the three arguments
above, along with the id value for an InstructorTask object.  The InstructorTask
object contains a 'task_input' row which is a JSON-encoded dict containing
a problem URL and optionally a student.  These are used to set up the initial value
of the query for traversing StudentModule objects.

"""

import logging
from functools import partial

from celery import shared_task
from django.utils.translation import ugettext_noop
from edx_django_utils.monitoring import set_code_owner_attribute

from openedx.features.wikimedia_features.admin_dashboard.tasks_base import BaseAdminReportTask
from openedx.features.wikimedia_features.admin_dashboard.grades import MultipleCourseGradeReport
from openedx.features.wikimedia_features.admin_dashboard.runner import run_main_task

TASK_LOG = logging.getLogger('edx.celery.task')

@shared_task(base=BaseAdminReportTask)
@set_code_owner_attribute
def task_calculate_grades_csv(entry_id, xmodule_instance_args):
    """
    Generate a grade report for multiple courses and push the results to an S3 bucket for download.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('graded')
    TASK_LOG.info(
        "Task: %s, AdminReportTask ID: %s, Task type: %s, Preparing for task execution",
        xmodule_instance_args.get('task_id'), entry_id, action_name
    )

    task_fn = partial(MultipleCourseGradeReport.generate, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)
