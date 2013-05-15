import json
import logging
from django.http import HttpResponse
from django.db import transaction

from celery.result import AsyncResult
from celery.states import READY_STATES

from courseware.models import CourseTaskLog
from courseware.module_render import get_xqueue_callback_url_prefix
from courseware.tasks import (regrade_problem_for_all_students, regrade_problem_for_student,
                              reset_problem_attempts_for_all_students, delete_problem_state_for_all_students)
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)


class AlreadyRunningError(Exception):
    pass


def get_running_course_tasks(course_id):
    """
    Returns a query of CourseTaskLog objects of running tasks for a given course.

    Used to generate a list of tasks to display on the instructor dashboard.
    """
    course_tasks = CourseTaskLog.objects.filter(course_id=course_id)
    for state in READY_STATES:
        course_tasks = course_tasks.exclude(task_state=state)
    return course_tasks


def course_task_log_status(request, task_id=None):
    """
    This returns the status of a course-related task as a JSON-serialized dict.

    The task_id can be specified in one of three ways:

    * explicitly as an argument to the method (by specifying in the url)
      Returns a dict containing status information for the specified task_id

    * by making a post request containing 'task_id' as a parameter with a single value
      Returns a dict containing status information for the specified task_id

    * by making a post request containing 'task_ids' as a parameter,
      with a list of task_id values.
      Returns a dict of dicts, with the task_id as key, and the corresponding
      dict containing status information for the specified task_id

      Task_id values that are unrecognized are skipped.

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

    return HttpResponse(json.dumps(output, indent=4))


def _task_is_running(course_id, task_name, task_args, student=None):
    """Checks if a particular task is already running"""
    runningTasks = CourseTaskLog.objects.filter(course_id=course_id, task_name=task_name, task_args=task_args)
    if student is not None:
        runningTasks = runningTasks.filter(student=student)
    for state in READY_STATES:
        runningTasks = runningTasks.exclude(task_state=state)
    return len(runningTasks) > 0


@transaction.autocommit
def _reserve_task(course_id, task_name, task_args, requester, student=None):
    """
    Creates a database entry to indicate that a task is in progress.

    An exception is thrown if the task is already in progress.

    Autocommit annotation makes sure the database entry is committed.
    """

    if _task_is_running(course_id, task_name, task_args, student):
        raise AlreadyRunningError("requested task is already running")

    # Create log entry now, so that future requests won't
    tasklog_args = {'course_id': course_id,
                    'task_name': task_name,
                    'task_args': task_args,
                    'task_state': 'QUEUING',
                    'requester': requester}
    if student is not None:
        tasklog_args['student'] = student

    course_task_log = CourseTaskLog.objects.create(**tasklog_args)
    return course_task_log


@transaction.autocommit
def _update_task(course_task_log, task_result):
    """
    Updates a database entry with information about the submitted task.

    Autocommit annotation makes sure the database entry is committed.
    """
    _update_course_task_log(course_task_log, task_result)


def _get_xmodule_instance_args(request):
    """
    Calculate parameters needed for instantiating xmodule instances.

    The `request_info` will be passed to a tracking log function, to provide information
    about the source of the task request.   The `xqueue_callback_urul_prefix` is used to
    permit old-style xqueue callbacks directly to the appropriate module in the LMS.
    """
    request_info = {'username': request.user.username,
                    'ip': request.META['REMOTE_ADDR'],
                    'agent': request.META.get('HTTP_USER_AGENT', ''),
                    'host': request.META['SERVER_NAME'],
                    }

    xmodule_instance_args = {'xqueue_callback_url_prefix': get_xqueue_callback_url_prefix(request),
                             'request_info': request_info,
                             }
    return xmodule_instance_args


def _update_course_task_log(course_task_log_entry, task_result):
    """
    Updates and possibly saves a CourseTaskLog entry based on a task Result.

    Used when a task initially returns, as well as when updated status is
    requested.

    Calculates json to store in task_progress field.
    """
    task_id = task_result.task_id
    result_state = task_result.state
    returned_result = task_result.result
    result_traceback = task_result.traceback

    # Assume we don't always update the CourseTaskLog entry if we don't have to:
    entry_needs_saving = False
    output = {}

    if result_state == 'PROGRESS':
        # construct a status message directly from the task result's result:
        if hasattr(task_result, 'result') and 'attempted' in returned_result:
            fmt = "Attempted {attempted} of {total}, {action_name} {updated}"
            message = fmt.format(attempted=returned_result['attempted'],
                                 updated=returned_result['updated'],
                                 total=returned_result['total'],
                                 action_name=returned_result['action_name'])
            output['message'] = message
            log.info("task progress: %s", message)
        else:
            log.info("still making progress... ")
        output['task_progress'] = returned_result

    elif result_state == 'SUCCESS':
        output['task_progress'] = returned_result
        course_task_log_entry.task_progress = json.dumps(returned_result)
        log.info("task succeeded: %s", returned_result)
        entry_needs_saving = True

    elif result_state == 'FAILURE':
        # on failure, the result's result contains the exception that caused the failure
        exception = returned_result
        traceback = result_traceback if result_traceback is not None else ''
        entry_needs_saving = True
        task_progress = {'exception': type(exception).__name__, 'message': str(exception.message)}
        output['message'] = exception.message
        log.warning("background task (%s) failed: %s %s", task_id, returned_result, traceback)
        if result_traceback is not None:
            output['task_traceback'] = result_traceback
            task_progress['traceback'] = result_traceback
        course_task_log_entry.task_progress = json.dumps(task_progress)
        output['task_progress'] = task_progress

    elif result_state == 'REVOKED':
        # on revocation, the result's result doesn't contain anything
        entry_needs_saving = True
        message = 'Task revoked before running'
        output['message'] = message
        log.warning("background task (%s) revoked.", task_id)
        task_progress = {'message': message}
        course_task_log_entry.task_progress = json.dumps(task_progress)
        output['task_progress'] = task_progress

    # always update the entry if the state has changed:
    if result_state != course_task_log_entry.task_state:
        course_task_log_entry.task_state = result_state
        course_task_log_entry.task_id = task_id
        entry_needs_saving = True

    if entry_needs_saving:
        course_task_log_entry.save()

    return output


def _get_course_task_log_status(task_id):
    """
    Get the status for a given task_id.

    Returns a dict, with the following keys:
      'task_id'
      'task_state'
      'in_progress': boolean indicating if the task is still running.
      'message': status message reporting on progress, or providing exception message if failed.
      'task_progress': dict containing progress information.  This includes:
          'attempted': number of attempts made
          'updated': number of attempts that "succeeded"
          'total': number of possible subtasks to attempt
          'action_name': user-visible verb to use in status messages.  Should be past-tense.
      'task_traceback': optional, returned if task failed and produced a traceback.
      'succeeded': on complete tasks, indicates if the task outcome was successful:
          did it achieve what it set out to do.
          This is in contrast with a successful task_state, which indicates that the
          task merely completed.

      If task doesn't exist, returns None.
    """
    # First check if the task_id is known
    try:
        course_task_log_entry = CourseTaskLog.objects.get(task_id=task_id)
    except CourseTaskLog.DoesNotExist:
        # TODO: log a message here
        return None

    # define ajax return value:
    output = {}

    # if the task is already known to be done, then there's no reason to query
    # the underlying task's result object:
    if course_task_log_entry.task_state not in READY_STATES:
        # we need to get information from the task result directly now.

        # Just create the result object, and pull values out once.
        # (If we check them later, the state and result may have changed.)
        result = AsyncResult(task_id)
        output.update(_update_course_task_log(course_task_log_entry, result))
    elif course_task_log_entry.task_progress is not None:
        # task is already known to have finished, but report on its status:
        output['task_progress'] = json.loads(course_task_log_entry.task_progress)
        if course_task_log_entry.task_state == 'FAILURE':
            output['message'] = output['task_progress']['message']

    # output basic information matching what's stored in CourseTaskLog:
    output['task_id'] = course_task_log_entry.task_id
    output['task_state'] = course_task_log_entry.task_state
    output['in_progress'] = course_task_log_entry.task_state not in READY_STATES

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
            msg = "Problem failed to be {action} for student '{student}' and problem '{problem}'"
        else:
            succeeded = True
            msg = "Problem successfully {action} for student '{student}' and problem '{problem}'"
    elif num_attempted == 0:
        msg = "Unable to find any students with submissions to be {action} for problem '{problem}'."
    elif num_updated == 0:
        msg = "Problem failed to be {action} for any of {attempted} students for problem '{problem}'"
    elif num_updated == num_attempted:
        succeeded = True
        msg = "Problem successfully {action} for {attempted} students for problem '{problem}'"
    elif num_updated < num_attempted:
        msg = "Problem {action} for {updated} of {attempted} students for problem '{problem}'"

    # Update status in task result object itself:
    message = msg.format(action=action_name, updated=num_updated, attempted=num_attempted,
                         student=course_task_log_entry.student, problem=course_task_log_entry.task_args)
    return (succeeded, message)


########### Add task-submission methods here:

def _check_arguments_for_regrading(course_id, problem_url):
    """
    Do simple checks on the descriptor to confirm that it supports regrading.

    Confirms first that the problem_url is defined (since that's currently typed
    in).  An ItemNotFoundException is raised if the corresponding module
    descriptor doesn't exist.  NotImplementedError is returned if the
    corresponding module doesn't support regrading calls.
    """
    descriptor = modulestore().get_instance(course_id, problem_url)
    supports_regrade = False
    if hasattr(descriptor, 'module_class'):
        module_class = descriptor.module_class
        if hasattr(module_class, 'regrade_problem'):
            supports_regrade = True

    if not supports_regrade:
        msg = "Specified module does not support regrading."
        raise NotImplementedError(msg)


def submit_regrade_problem_for_student(request, course_id, problem_url, student):
    """
    Request a problem to be regraded as a background task.

    The problem will be regraded for the specified student only.  Parameters are the `course_id`,
    the `problem_url`, and the `student` as a User object.
    The url must specify the location of the problem, using i4x-type notation.

    An exception is thrown if the problem doesn't exist, or if the particular
    problem is already being regraded for this student.
    """
    # check arguments:  let exceptions return up to the caller. 
    _check_arguments_for_regrading(course_id, problem_url)

    task_name = 'regrade_problem'

    # check to see if task is already running, and reserve it otherwise
    course_task_log = _reserve_task(course_id, task_name, problem_url, request.user, student)

    # Submit task:
    task_args = [course_id, problem_url, student.username, _get_xmodule_instance_args(request)]
    task_result = regrade_problem_for_student.apply_async(task_args)

    # Update info in table with the resulting task_id (and state).
    _update_task(course_task_log, task_result)

    return course_task_log


def submit_regrade_problem_for_all_students(request, course_id, problem_url):
    """
    Request a problem to be regraded as a background task.

    The problem will be regraded for all students who have accessed the
    particular problem in a course and have provided and checked an answer.
    Parameters are the `course_id` and the `problem_url`.
    The url must specify the location of the problem, using i4x-type notation.

    An exception is thrown if the problem doesn't exist, or if the particular
    problem is already being regraded.
    """
    # check arguments:  let exceptions return up to the caller.
    _check_arguments_for_regrading(course_id, problem_url)

    # check to see if task is already running, and reserve it otherwise
    task_name = 'regrade_problem'
    course_task_log = _reserve_task(course_id, task_name, problem_url, request.user)

    # Submit task:
    task_args = [course_id, problem_url, _get_xmodule_instance_args(request)]
    task_result = regrade_problem_for_all_students.apply_async(task_args)

    # Update info in table with the resulting task_id (and state).
    _update_task(course_task_log, task_result)

    return course_task_log


def submit_reset_problem_attempts_for_all_students(request, course_id, problem_url):
    """
    Request to have attempts reset for a problem as a background task.

    The problem's attempts will be reset for all students who have accessed the
    particular problem in a course.  Parameters are the `course_id` and
    the `problem_url`.  The url must specify the location of the problem,
    using i4x-type notation.

    An exception is thrown if the problem doesn't exist, or if the particular
    problem is already being reset.
    """
    # check arguments:  make sure that the problem_url is defined
    # (since that's currently typed in).  If the corresponding module descriptor doesn't exist,
    # an exception will be raised.  Let it pass up to the caller.
    modulestore().get_instance(course_id, problem_url)

    task_name = 'reset_problem_attempts'

    # check to see if task is already running, and reserve it otherwise
    course_task_log = _reserve_task(course_id, task_name, problem_url, request.user)

    # Submit task:
    task_args = [course_id, problem_url, _get_xmodule_instance_args(request)]
    task_result = reset_problem_attempts_for_all_students.apply_async(task_args)

    # Update info in table with the resulting task_id (and state).
    _update_task(course_task_log, task_result)

    return course_task_log


def submit_delete_problem_state_for_all_students(request, course_id, problem_url):
    """
    Request to have state deleted for a problem as a background task.

    The problem's state will be deleted for all students who have accessed the
    particular problem in a course.  Parameters are the `course_id` and
    the `problem_url`.  The url must specify the location of the problem,
    using i4x-type notation.

    An exception is thrown if the problem doesn't exist, or if the particular
    problem is already being deleted.
    """
    # check arguments:  make sure that the problem_url is defined
    # (since that's currently typed in).  If the corresponding module descriptor doesn't exist,
    # an exception will be raised.  Let it pass up to the caller.
    modulestore().get_instance(course_id, problem_url)

    task_name = 'delete_problem_state'

    # check to see if task is already running, and reserve it otherwise
    course_task_log = _reserve_task(course_id, task_name, problem_url, request.user)

    # Submit task:
    task_args = [course_id, problem_url, _get_xmodule_instance_args(request)]
    task_result = delete_problem_state_for_all_students.apply_async(task_args)

    # Update info in table with the resulting task_id (and state).
    _update_task(course_task_log, task_result)

    return course_task_log
