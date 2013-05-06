import json
import logging
from django.http import HttpResponse

from celery.result import AsyncResult
from celery.states import READY_STATES

from courseware.models import CourseTaskLog
from courseware.tasks import regrade_problem_for_all_students
from xmodule.modulestore.django import modulestore


# define different loggers for use within tasks and on client side
log = logging.getLogger(__name__)


def get_running_course_tasks(course_id):
    course_tasks = CourseTaskLog.objects.filter(course_id=course_id)
    # exclude(task_state='SUCCESS').exclude(task_state='FAILURE').exclude(task_state='REVOKED')
    for state in READY_STATES:
        course_tasks = course_tasks.exclude(task_state=state)
    return course_tasks


def _task_is_running(course_id, task_name, task_args, student=None):
    runningTasks = CourseTaskLog.objects.filter(course_id=course_id, task_name=task_name, task_args=task_args)
    if student is not None:
        runningTasks = runningTasks.filter(student=student)
    for state in READY_STATES:
        runningTasks = runningTasks.exclude(task_state=state)
    return len(runningTasks) > 0


def submit_regrade_problem_for_all_students(request, course_id, problem_url):
    # check arguments: in particular, make sure that problem_url is defined
    # (since that's currently typed in).  If the corresponding module descriptor doesn't exist, 
    # an exception should be raised.  Let it continue to the caller.
    modulestore().get_instance(course_id, problem_url)

    # TODO: adjust transactions so that one request will not be about to create an
    # entry while a second is testing to see if the entry exists.  (Need to handle
    # quick accidental double-clicks when submitting.)

    # check to see if task is already running
    task_name = 'regrade'
    if _task_is_running(course_id, task_name, problem_url):
        # TODO: figure out how to return info that it's already running
        raise Exception("task is already running")

    # Create log entry now, so that future requests won't
    tasklog_args = {'course_id': course_id,
                    'task_name': task_name,
                    'task_args': problem_url,
                    'task_state': 'QUEUING',
                    'requester': request.user}
    course_task_log = CourseTaskLog.objects.create(**tasklog_args)


    # At a low level of processing, the task currently fetches some information from the web request. 
    # This is used for setting up X-Queue, as well as for tracking.
    # An actual request will not successfully serialize with json or with pickle.
    # TODO: we can just pass all META info as a dict.
    request_environ = {'HTTP_USER_AGENT': request.META['HTTP_USER_AGENT'],
                       'REMOTE_ADDR': request.META['REMOTE_ADDR'],
                       'SERVER_NAME': request.META['SERVER_NAME'],
                       'REQUEST_METHOD': 'GET',
#                      'HTTP_X_FORWARDED_PROTO': request.META['HTTP_X_FORWARDED_PROTO'],
                      }

    # Submit task:
    task_args = [request_environ, course_id, problem_url]
    result = regrade_problem_for_all_students.apply_async(task_args)

    # Put info into table with the resulting task_id.
    course_task_log.task_state = result.state
    course_task_log.task_id = result.id
    course_task_log.save()
    return course_task_log


def course_task_log_status(request, task_id=None):
    """
    This returns the status of a course-related task as a JSON-serialized dict.
    """
    output = {}
    if task_id is not None:
        output = _get_course_task_log_status(task_id)
    elif 'task_id' in request.POST:
        task_id = request.POST['task_id']
        output = _get_course_task_log_status(task_id)
    elif 'task_ids[]' in request.POST:
        tasks = request.POST.getlist('task_ids[]')
        for task_id in tasks:
            task_output = _get_course_task_log_status(task_id)
            if task_output is not None:
                output[task_id] = task_output
    # TODO decide whether to raise exception if bad args are passed.
    # May be enough just to return an empty output.

    return HttpResponse(json.dumps(output, indent=4))


def _get_course_task_log_status(task_id):
    """
    Get the status for a given task_id.

    Returns a dict, with the following keys:
      'task_id'
      'task_state'
      'in_progress': boolean indicating if the task is still running.
      'task_traceback': optional, returned if task failed and produced a traceback.

      If task doesn't exist, returns None.
    """
    # First check if the task_id is known
    try:
        course_task_log_entry = CourseTaskLog.objects.get(task_id=task_id)
    except CourseTaskLog.DoesNotExist:
        # TODO: log a message here
        return None

    output = {}

    # if the task is already known to be done, then there's no reason to query
    # the underlying task:
    if course_task_log_entry.task_state not in READY_STATES:
        # we need to get information from the task result directly now.
        # Just create the result object.
        result = AsyncResult(task_id)

        if result.traceback is not None:
            output['task_traceback'] = result.traceback

        if result.state == "PROGRESS":
            # construct a status message directly from the task result's metadata:
            if hasattr(result, 'result') and 'current' in result.result:
                fmt = "Attempted {attempted} of {total}, {action_name} {updated}"
                message = fmt.format(attempted=result.result['attempted'],
                                     updated=result.result['updated'],
                                     total=result.result['total'],
                                     action_name=result.result['action_name'])
                output['message'] = message
                log.info("progress: {0}".format(message))
                for name in ['attempted', 'updated', 'total', 'action_name']:
                    output[name] = result.result[name]
            else:
                log.info("still making progress... ")

        # update the entry if the state has changed:
        if result.state != course_task_log_entry.task_state:
            course_task_log_entry.task_state = result.state
            course_task_log_entry.save()

    output['task_id'] = course_task_log_entry.task_id
    output['task_state'] = course_task_log_entry.task_state
    output['in_progress'] = course_task_log_entry.task_state not in READY_STATES

    if course_task_log_entry.task_progress is not None:
        output['task_progress'] = course_task_log_entry.task_progress

    if course_task_log_entry.task_state == 'SUCCESS':
        succeeded, message = _get_task_completion_message(course_task_log_entry)
        output['message'] = message
        output['succeeded'] = succeeded

    return output


def _get_task_completion_message(course_task_log_entry):
    """
    Construct progress message from progress information in CourseTaskLog entry.

    Returns (boolean, message string) duple.
    """
    succeeded = False

    if course_task_log_entry.task_progress is None:
        log.warning("No task_progress information found for course_task {0}".format(course_task_log_entry.task_id))
        return (succeeded, "No status information available")

    task_progress = json.loads(course_task_log_entry.task_progress)
    action_name = task_progress['action_name']
    num_attempted = task_progress['attempted']
    num_updated = task_progress['updated']
    # num_total = task_progress['total']
    if course_task_log_entry.student is not None:
        if num_attempted == 0:
            msg = "Unable to find submission to be {action} for student '{student}' and problem '{problem}'."
        elif num_updated == 0:
            msg = "Problem failed to be {action} for student '{student}' and problem '{problem}'!"
        else:
            succeeded = True
            msg = "Problem successfully {action} for student '{student}' and problem '{problem}'"
    elif num_attempted == 0:
        msg = "Unable to find any students with submissions to be {action} for problem '{problem}'."
    elif num_updated == 0:
        msg = "Problem failed to be {action} for any of {attempted} students for problem '{problem}'!"
    elif num_updated == num_attempted:
        succeeded = True
        msg = "Problem successfully {action} for {attempted} students for problem '{problem}'!"
    elif num_updated < num_attempted:
        msg = "Problem {action} for {updated} of {attempted} students for problem '{problem}'!"

    # Update status in task result object itself:
    message = msg.format(action=action_name, updated=num_updated, attempted=num_attempted, 
                         student=course_task_log_entry.student, problem=course_task_log_entry.task_args)
    return (succeeded, message)
