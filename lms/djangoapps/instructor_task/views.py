
import json
import logging

from django.http import HttpResponse

from celery.states import FAILURE, REVOKED, READY_STATES

from instructor_task.api_helper import (_get_instructor_task_status,
                                        _get_updated_instructor_task)


log = logging.getLogger(__name__)


def instructor_task_status(request):
    """
    View method that returns the status of a course-related task or tasks.

    Status is returned as a JSON-serialized dict, wrapped as the content of a HTTPResponse.

    The task_id can be specified to this view in one of three ways:

    * by making a request containing 'task_id' as a parameter with a single value
      Returns a dict containing status information for the specified task_id

    * by making a request containing 'task_ids' as a parameter,
      with a list of task_id values.
      Returns a dict of dicts, with the task_id as key, and the corresponding
      dict containing status information for the specified task_id

      Task_id values that are unrecognized are skipped.

    """
    def get_instructor_task_status(task_id):
        instructor_task = _get_updated_instructor_task(task_id)
        status = _get_instructor_task_status(instructor_task)
        if instructor_task.task_state in READY_STATES:
            succeeded, message = get_task_completion_info(instructor_task)
            status['message'] = message
            status['succeeded'] = succeeded
        return status

    output = {}
    if 'task_id' in request.REQUEST:
        task_id = request.REQUEST['task_id']
        output = get_instructor_task_status(task_id)
    elif 'task_ids[]' in request.REQUEST:
        tasks = request.REQUEST.getlist('task_ids[]')
        for task_id in tasks:
            task_output = get_instructor_task_status(task_id)
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

    if instructor_task.task_output is None:
        log.warning("No task_output information found for instructor_task {0}".format(instructor_task.task_id))
        return (succeeded, "No status information available")

    task_output = json.loads(instructor_task.task_output)
    if instructor_task.task_state in [FAILURE, REVOKED]:
        return(succeeded, task_output['message'])

    action_name = task_output['action_name']
    num_attempted = task_output['attempted']
    num_updated = task_output['updated']
    num_total = task_output['total']

    if instructor_task.task_input is None:
        log.warning("No task_input information found for instructor_task {0}".format(instructor_task.task_id))
        return (succeeded, "No status information available")
    task_input = json.loads(instructor_task.task_input)
    problem_url = task_input.get('problem_url')
    student = task_input.get('student')
    if student is not None:
        if num_attempted == 0:
            msg_format = "Unable to find submission to be {action} for student '{student}'"
        elif num_updated == 0:
            msg_format = "Problem failed to be {action} for student '{student}'"
        else:
            succeeded = True
            msg_format = "Problem successfully {action} for student '{student}'"
    elif num_attempted == 0:
        msg_format = "Unable to find any students with submissions to be {action}"
    elif num_updated == 0:
        msg_format = "Problem failed to be {action} for any of {attempted} students"
    elif num_updated == num_attempted:
        succeeded = True
        msg_format = "Problem successfully {action} for {attempted} students"
    else:  # num_updated < num_attempted
        msg_format = "Problem {action} for {updated} of {attempted} students"

    if student is not None and num_attempted != num_total:
        msg_format += " (out of {total})"

    # Update status in task result object itself:
    message = msg_format.format(action=action_name, updated=num_updated, attempted=num_attempted, total=num_total,
                                student=student, problem=problem_url)
    return (succeeded, message)
