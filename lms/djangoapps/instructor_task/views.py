
import json
import logging

from django.http import HttpResponse

from celery.states import FAILURE, REVOKED, READY_STATES

from instructor_task.api_helper import (get_status_from_instructor_task,
                                        get_updated_instructor_task)
from instructor_task.models import PROGRESS


log = logging.getLogger(__name__)

# return status for completed tasks and tasks in progress
STATES_WITH_STATUS = [state for state in READY_STATES] + [PROGRESS]


def _get_instructor_task_status(task_id):
    """
    Returns status for a specific task.

    Written as an internal method here (rather than as a helper)
    so that get_task_completion_info() can be called without
    causing a circular dependency (since it's also called directly).
    """
    instructor_task = get_updated_instructor_task(task_id)
    status = get_status_from_instructor_task(instructor_task)
    if instructor_task is not None and instructor_task.task_state in STATES_WITH_STATUS:
        succeeded, message = get_task_completion_info(instructor_task)
        status['message'] = message
        status['succeeded'] = succeeded
    return status


def instructor_task_status(request):
    """
    View method that returns the status of a course-related task or tasks.

    Status is returned as a JSON-serialized dict, wrapped as the content of a HTTPResponse.

    The task_id can be specified to this view in one of two ways:

    * by making a request containing 'task_id' as a parameter with a single value
      Returns a dict containing status information for the specified task_id

    * by making a request containing 'task_ids' as a parameter,
      with a list of task_id values.
      Returns a dict of dicts, with the task_id as key, and the corresponding
      dict containing status information for the specified task_id

      Task_id values that are unrecognized are skipped.

    The dict with status information for a task contains the following keys:
      'message': on complete tasks, status message reporting on final progress,
          or providing exception message if failed.  For tasks in progress,
          indicates the current progress.
      'succeeded': on complete tasks or tasks in progress, boolean value indicates if the
          task outcome was successful:  did it achieve what it set out to do.
          This is in contrast with a successful task_state, which indicates that the
          task merely completed.
      'task_id': id assigned by LMS and used by celery.
      'task_state': state of task as stored in celery's result store.
      'in_progress': boolean indicating if task is still running.
      'task_progress': dict containing progress information.  This includes:
          'attempted': number of attempts made
          'succeeded': number of attempts that "succeeded"
          'total': number of possible subtasks to attempt
          'action_name': user-visible verb to use in status messages.  Should be past-tense.
          'duration_ms': how long the task has (or had) been running.
          'exception': name of exception class raised in failed tasks.
          'message': returned for failed and revoked tasks.
          'traceback': optional, returned if task failed and produced a traceback.

    """

    output = {}
    if 'task_id' in request.REQUEST:
        task_id = request.REQUEST['task_id']
        output = _get_instructor_task_status(task_id)
    elif 'task_ids[]' in request.REQUEST:
        tasks = request.REQUEST.getlist('task_ids[]')
        for task_id in tasks:
            task_output = _get_instructor_task_status(task_id)
            if task_output is not None:
                output[task_id] = task_output

    return HttpResponse(json.dumps(output, indent=4))


def get_task_completion_info(instructor_task):
    """
    Construct progress message from progress information in InstructorTask entry.

    Returns (boolean, message string) duple, where the boolean indicates
    whether the task completed without incident.  (It is possible for a
    task to attempt many sub-tasks, such as rescoring many students' problem
    responses, and while the task runs to completion, some of the students'
    responses could not be rescored.)

    Used for providing messages to instructor_task_status(), as well as
    external calls for providing course task submission history information.
    """
    succeeded = False

    if instructor_task.task_state not in STATES_WITH_STATUS:
        return (succeeded, "No status information available")

    # we're more surprised if there is no output for a completed task, but just warn:
    if instructor_task.task_output is None:
        log.warning("No task_output information found for instructor_task {0}".format(instructor_task.task_id))
        return (succeeded, "No status information available")

    try:
        task_output = json.loads(instructor_task.task_output)
    except ValueError:
        fmt = "No parsable task_output information found for instructor_task {0}: {1}"
        log.warning(fmt.format(instructor_task.task_id, instructor_task.task_output))
        return (succeeded, "No parsable status information available")

    if instructor_task.task_state in [FAILURE, REVOKED]:
        return (succeeded, task_output.get('message', 'No message provided'))

    if any([key not in task_output for key in ['action_name', 'attempted', 'total']]):
        fmt = "Invalid task_output information found for instructor_task {0}: {1}"
        log.warning(fmt.format(instructor_task.task_id, instructor_task.task_output))
        return (succeeded, "No progress status information available")

    action_name = task_output['action_name']
    num_attempted = task_output['attempted']
    num_total = task_output['total']

    # old tasks may still have 'updated' instead of the preferred 'succeeded':
    num_succeeded = task_output.get('updated', 0) + task_output.get('succeeded', 0)
    num_skipped = task_output.get('skipped', 0)
    # num_failed = task_output.get('failed', 0)

    student = None
    problem_url = None
    email_id = None
    try:
        task_input = json.loads(instructor_task.task_input)
    except ValueError:
        fmt = "No parsable task_input information found for instructor_task {0}: {1}"
        log.warning(fmt.format(instructor_task.task_id, instructor_task.task_input))
    else:
        student = task_input.get('student')
        problem_url = task_input.get('problem_url')
        email_id = task_input.get('email_id')

    if instructor_task.task_state == PROGRESS:
        # special message for providing progress updates:
        msg_format = "Progress: {action} {succeeded} of {attempted} so far"
    elif student is not None and problem_url is not None:
        # this reports on actions on problems for a particular student:
        if num_attempted == 0:
            msg_format = "Unable to find submission to be {action} for student '{student}'"
        elif num_succeeded == 0:
            msg_format = "Problem failed to be {action} for student '{student}'"
        else:
            succeeded = True
            msg_format = "Problem successfully {action} for student '{student}'"
    elif student is None and problem_url is not None:
        # this reports on actions on problems for all students:
        if num_attempted == 0:
            msg_format = "Unable to find any students with submissions to be {action}"
        elif num_succeeded == 0:
            msg_format = "Problem failed to be {action} for any of {attempted} students"
        elif num_succeeded == num_attempted:
            succeeded = True
            msg_format = "Problem successfully {action} for {attempted} students"
        else:  # num_succeeded < num_attempted
            msg_format = "Problem {action} for {succeeded} of {attempted} students"
    elif email_id is not None:
        # this reports on actions on bulk emails
        if num_attempted == 0:
            msg_format = "Unable to find any recipients to be {action}"
        elif num_succeeded == 0:
            msg_format = "Message failed to be {action} for any of {attempted} recipients "
        elif num_succeeded == num_attempted:
            succeeded = True
            msg_format = "Message successfully {action} for {attempted} recipients"
        else:  # num_succeeded < num_attempted
            msg_format = "Message {action} for {succeeded} of {attempted} recipients"
    else:
        # provide a default:
        msg_format = "Status: {action} {succeeded} of {attempted}"

    if num_skipped > 0:
        msg_format += " (skipping {skipped})"

    if student is None and num_attempted != num_total:
        msg_format += " (out of {total})"

    # Update status in task result object itself:
    message = msg_format.format(
        action=action_name,
        succeeded=num_succeeded,
        attempted=num_attempted,
        total=num_total,
        skipped=num_skipped,
        student=student)
    return (succeeded, message)
