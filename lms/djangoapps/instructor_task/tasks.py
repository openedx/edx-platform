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

from django.conf import settings
from django.utils.translation import ugettext_noop

from celery import task
from bulk_email.tasks import perform_delegate_email_batches
from instructor_task.tasks_helper import (
    run_main_task,
    BaseInstructorTask,
    perform_module_state_update,
    rescore_problem_module_state,
    reset_attempts_module_state,
    delete_problem_module_state,
    upload_grades_csv,
    upload_problem_grade_report,
    upload_students_csv,
    cohort_students_and_upload,
    upload_enrollment_report,
    upload_may_enroll_csv,
    upload_exec_summary_report,
    generate_students_certificates,
)


TASK_LOG = logging.getLogger('edx.celery.task')


@task(base=BaseInstructorTask)  # pylint: disable=not-callable
def rescore_problem(entry_id, xmodule_instance_args):
    """Rescores a problem in a course, for all students or one specific student.

    `entry_id` is the id value of the InstructorTask entry that corresponds to this task.
    The entry contains the `course_id` that identifies the course, as well as the
    `task_input`, which contains task-specific input.

    The task_input should be a dict with the following entries:

      'problem_url': the full URL to the problem to be rescored.  (required)

      'student': the identifier (username or email) of a particular user whose
          problem submission should be rescored.  If not specified, all problem
          submissions for the problem will be rescored.

    `xmodule_instance_args` provides information needed by _get_module_instance_for_task()
    to instantiate an xmodule instance.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('rescored')
    update_fcn = partial(rescore_problem_module_state, xmodule_instance_args)

    def filter_fcn(modules_to_update):
        """Filter that matches problems which are marked as being done"""
        return modules_to_update.filter(state__contains='"done": true')

    visit_fcn = partial(perform_module_state_update, update_fcn, filter_fcn)
    return run_main_task(entry_id, visit_fcn, action_name)


@task(base=BaseInstructorTask)  # pylint: disable=not-callable
def reset_problem_attempts(entry_id, xmodule_instance_args):
    """Resets problem attempts to zero for a particular problem for all students in a course.

    `entry_id` is the id value of the InstructorTask entry that corresponds to this task.
    The entry contains the `course_id` that identifies the course, as well as the
    `task_input`, which contains task-specific input.

    The task_input should be a dict with the following entries:

      'problem_url': the full URL to the problem to be rescored.  (required)

    `xmodule_instance_args` provides information needed by _get_module_instance_for_task()
    to instantiate an xmodule instance.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('reset')
    update_fcn = partial(reset_attempts_module_state, xmodule_instance_args)
    visit_fcn = partial(perform_module_state_update, update_fcn, None)
    return run_main_task(entry_id, visit_fcn, action_name)


@task(base=BaseInstructorTask)  # pylint: disable=not-callable
def delete_problem_state(entry_id, xmodule_instance_args):
    """Deletes problem state entirely for all students on a particular problem in a course.

    `entry_id` is the id value of the InstructorTask entry that corresponds to this task.
    The entry contains the `course_id` that identifies the course, as well as the
    `task_input`, which contains task-specific input.

    The task_input should be a dict with the following entries:

      'problem_url': the full URL to the problem to be rescored.  (required)

    `xmodule_instance_args` provides information needed by _get_module_instance_for_task()
    to instantiate an xmodule instance.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('deleted')
    update_fcn = partial(delete_problem_module_state, xmodule_instance_args)
    visit_fcn = partial(perform_module_state_update, update_fcn, None)
    return run_main_task(entry_id, visit_fcn, action_name)


@task(base=BaseInstructorTask)  # pylint: disable=not-callable
def send_bulk_course_email(entry_id, _xmodule_instance_args):
    """Sends emails to recipients enrolled in a course.

    `entry_id` is the id value of the InstructorTask entry that corresponds to this task.
    The entry contains the `course_id` that identifies the course, as well as the
    `task_input`, which contains task-specific input.

    The task_input should be a dict with the following entries:

      'email_id': the full URL to the problem to be rescored.  (required)

    `_xmodule_instance_args` provides information needed by _get_module_instance_for_task()
    to instantiate an xmodule instance.  This is unused here.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('emailed')
    visit_fcn = perform_delegate_email_batches
    return run_main_task(entry_id, visit_fcn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)  # pylint: disable=not-callable
def calculate_grades_csv(entry_id, xmodule_instance_args):
    """
    Grade a course and push the results to an S3 bucket for download.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('graded')
    TASK_LOG.info(
        u"Task: %s, InstructorTask ID: %s, Task type: %s, Preparing for task execution",
        xmodule_instance_args.get('task_id'), entry_id, action_name
    )

    task_fn = partial(upload_grades_csv, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)  # pylint: disable=not-callable
def calculate_problem_grade_report(entry_id, xmodule_instance_args):
    """
    Generate a CSV for a course containing all students' problem
    grades and push the results to an S3 bucket for download.
    """
    # Translators: This is a past-tense phrase that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('problem distribution graded')
    TASK_LOG.info(
        u"Task: %s, InstructorTask ID: %s, Task type: %s, Preparing for task execution",
        xmodule_instance_args.get('task_id'), entry_id, action_name
    )

    task_fn = partial(upload_problem_grade_report, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)  # pylint: disable=not-callable
def calculate_students_features_csv(entry_id, xmodule_instance_args):
    """
    Compute student profile information for a course and upload the
    CSV to an S3 bucket for download.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('generated')
    task_fn = partial(upload_students_csv, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)  # pylint: disable=not-callable
def enrollment_report_features_csv(entry_id, xmodule_instance_args):
    """
    Compute student profile information for a course and upload the
    CSV to an S3 bucket for download.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('generating_enrollment_report')
    task_fn = partial(upload_enrollment_report, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)  # pylint: disable=not-callable
def exec_summary_report_csv(entry_id, xmodule_instance_args):
    """
    Compute executive summary report for a course and upload the
    Html generated report to an S3 bucket for download.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = 'generating_exec_summary_report'
    task_fn = partial(upload_exec_summary_report, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)  # pylint: disable=not-callable
def calculate_may_enroll_csv(entry_id, xmodule_instance_args):
    """
    Compute information about invited students who have not enrolled
    in a given course yet and upload the CSV to an S3 bucket for
    download.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('generated')
    task_fn = partial(upload_may_enroll_csv, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask, routing_key=settings.GRADES_DOWNLOAD_ROUTING_KEY)  # pylint: disable=not-callable
def generate_certificates(entry_id, xmodule_instance_args):
    """
    Grade students and generate certificates.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    action_name = ugettext_noop('certificates generated')
    TASK_LOG.info(
        u"Task: %s, InstructorTask ID: %s, Task type: %s, Preparing for task execution",
        xmodule_instance_args.get('task_id'), entry_id, action_name
    )

    task_fn = partial(generate_students_certificates, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)


@task(base=BaseInstructorTask)  # pylint: disable=E1102
def cohort_students(entry_id, xmodule_instance_args):
    """
    Cohort students in bulk, and upload the results.
    """
    # Translators: This is a past-tense verb that is inserted into task progress messages as {action}.
    # An example of such a message is: "Progress: {action} {succeeded} of {attempted} so far"
    action_name = ugettext_noop('cohorted')
    task_fn = partial(cohort_students_and_upload, xmodule_instance_args)
    return run_main_task(entry_id, task_fn, action_name)
