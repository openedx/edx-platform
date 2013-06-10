import hashlib
import json
import logging
# from django.http import HttpResponse
from django.db import transaction

from celery.result import AsyncResult
from celery.states import READY_STATES, SUCCESS, FAILURE, REVOKED

from courseware.module_render import get_xqueue_callback_url_prefix

from xmodule.modulestore.django import modulestore
from instructor_task.models import InstructorTask
# from instructor_task.views import get_task_completion_info
from instructor_task.tasks_helper import PROGRESS


log = logging.getLogger(__name__)

# define a "state" used in InstructorTask
QUEUING = 'QUEUING'


class AlreadyRunningError(Exception):
    pass


def _task_is_running(course_id, task_type, task_key):
    """Checks if a particular task is already running"""
    runningTasks = InstructorTask.objects.filter(course_id=course_id, task_type=task_type, task_key=task_key)
    # exclude states that are "ready" (i.e. not "running", e.g. failure, success, revoked):
    for state in READY_STATES:
        runningTasks = runningTasks.exclude(task_state=state)
    return len(runningTasks) > 0


@transaction.autocommit
def _reserve_task(course_id, task_type, task_key, task_input, requester):
    """
    Creates a database entry to indicate that a task is in progress.

    Throws AlreadyRunningError if the task is already in progress.

    Autocommit annotation makes sure the database entry is committed.
    """

    if _task_is_running(course_id, task_type, task_key):
        raise AlreadyRunningError("requested task is already running")

    # Create log entry now, so that future requests won't:  no task_id yet....
    tasklog_args = {'course_id': course_id,
                    'task_type': task_type,
                    'task_key': task_key,
                    'task_input': json.dumps(task_input),
                    'task_state': 'QUEUING',
                    'requester': requester}

    instructor_task = InstructorTask.objects.create(**tasklog_args)
    return instructor_task


@transaction.autocommit
def _update_task(instructor_task, task_result):
    """
    Updates a database entry with information about the submitted task.

    Autocommit annotation makes sure the database entry is committed.
    """
    # we at least update the entry with the task_id, and for ALWAYS_EAGER mode,
    # we update other status as well.  (For non-ALWAYS_EAGER modes, the entry
    # should not have changed except for setting PENDING state and the
    # addition of the task_id.)
    _update_instructor_task(instructor_task, task_result)
    instructor_task.save()


def _get_xmodule_instance_args(request):
    """
    Calculate parameters needed for instantiating xmodule instances.

    The `request_info` will be passed to a tracking log function, to provide information
    about the source of the task request.   The `xqueue_callback_url_prefix` is used to
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


def _update_instructor_task(instructor_task, task_result):
    """
    Updates and possibly saves a InstructorTask entry based on a task Result.

    Used when a task initially returns, as well as when updated status is
    requested.

    The `instructor_task` that is passed in is updated in-place, but
    is usually not saved.  In general, tasks that have finished (either with
    success or failure) should have their entries updated by the task itself,
    so are not updated here.  Tasks that are still running are not updated
    while they run.  So the one exception to the no-save rule are tasks that
    are in a "revoked" state.  This may mean that the task never had the
    opportunity to update the InstructorTask entry.

    Calculates json to store in "task_output" field of the `instructor_task`,
    as well as updating the task_state and task_id (which may not yet be set
    if this is the first call after the task is submitted).

TODO: Update -- no longer return anything, or maybe the resulting instructor_task.

    Returns a dict, with the following keys:
      'message': status message reporting on progress, or providing exception message if failed.
      'task_progress': dict containing progress information.  This includes:
          'attempted': number of attempts made
          'updated': number of attempts that "succeeded"
          'total': number of possible subtasks to attempt
          'action_name': user-visible verb to use in status messages.  Should be past-tense.
          'duration_ms': how long the task has (or had) been running.
      'task_traceback': optional, returned if task failed and produced a traceback.
      'succeeded': on complete tasks, indicates if the task outcome was successful:
          did it achieve what it set out to do.
          This is in contrast with a successful task_state, which indicates that the
          task merely completed.

    """
    # Pull values out of the result object as close to each other as possible.
    # If we wait and check the values later, the values for the state and result
    # are more likely to have changed.  Pull the state out first, and
    # then code assuming that the result may not exactly match the state.
    task_id = task_result.task_id
    result_state = task_result.state
    returned_result = task_result.result
    result_traceback = task_result.traceback

    # Assume we don't always update the InstructorTask entry if we don't have to:
    entry_needs_saving = False
    output = {}

    if result_state in [PROGRESS, SUCCESS]:
        # construct a status message directly from the task result's result:
        # it needs to go back with the entry passed in.
        instructor_task.task_output = json.dumps(returned_result)
#        output['task_progress'] = returned_result
        log.info("background task (%s), succeeded: %s", task_id, returned_result)

    elif result_state == FAILURE:
        # on failure, the result's result contains the exception that caused the failure
        exception = returned_result
        traceback = result_traceback if result_traceback is not None else ''
        task_progress = {'exception': type(exception).__name__, 'message': str(exception.message)}
#        output['message'] = exception.message
        log.warning("background task (%s) failed: %s %s", task_id, returned_result, traceback)
        if result_traceback is not None:
#            output['task_traceback'] = result_traceback
            # truncate any traceback that goes into the InstructorTask model:
            task_progress['traceback'] = result_traceback[:700]
        # save progress into the entry, even if it's not being saved:
        # when celery is run in "ALWAYS_EAGER" mode, progress needs to go back
        # with the entry passed in.
        instructor_task.task_output = json.dumps(task_progress)
#        output['task_progress'] = task_progress

    elif result_state == REVOKED:
        # on revocation, the result's result doesn't contain anything
        # but we cannot rely on the worker thread to set this status,
        # so we set it here.
        entry_needs_saving = True
        message = 'Task revoked before running'
#        output['message'] = message
        log.warning("background task (%s) revoked.", task_id)
        task_progress = {'message': message}
        instructor_task.task_output = json.dumps(task_progress)
#        output['task_progress'] = task_progress

    # Always update the local version of the entry if the state has changed.
    # This is important for getting the task_id into the initial version
    # of the instructor_task, and also for development environments
    # when this code is executed when celery is run in "ALWAYS_EAGER" mode.
    if result_state != instructor_task.task_state:
        instructor_task.task_state = result_state
        instructor_task.task_id = task_id

    if entry_needs_saving:
        instructor_task.save()

    return output


def _get_updated_instructor_task(task_id):
    # First check if the task_id is known
    try:
        instructor_task = InstructorTask.objects.get(task_id=task_id)
    except InstructorTask.DoesNotExist:
        log.warning("query for InstructorTask status failed: task_id=(%s) not found", task_id)
        return None

    # if the task is not already known to be done, then we need to query
    # the underlying task's result object:
    if instructor_task.task_state not in READY_STATES:
        result = AsyncResult(task_id)
        _update_instructor_task(instructor_task, result)

    return instructor_task


# def _get_instructor_task_status(task_id):
def _get_instructor_task_status(instructor_task):
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
          'duration_ms': how long the task has (or had) been running.
      'task_traceback': optional, returned if task failed and produced a traceback.
      'succeeded': on complete tasks, indicates if the task outcome was successful:
          did it achieve what it set out to do.
          This is in contrast with a successful task_state, which indicates that the
          task merely completed.

      If task doesn't exist, returns None.

      If task has been REVOKED, the InstructorTask entry will be updated.
    """
#     # First check if the task_id is known
#     try:
#         instructor_task = InstructorTask.objects.get(task_id=task_id)
#     except InstructorTask.DoesNotExist:
#         log.warning("query for InstructorTask status failed: task_id=(%s) not found", task_id)
#         return None

    status = {}

    # if the task is not already known to be done, then we need to query
    # the underlying task's result object:
#     if instructor_task.task_state not in READY_STATES:
#         result = AsyncResult(task_id)
#         status.update(_update_instructor_task(instructor_task, result))

#    elif instructor_task.task_output is not None:
        # task is already known to have finished, but report on its status:
    if instructor_task.task_output is not None:
        status['task_progress'] = json.loads(instructor_task.task_output)

    # status basic information matching what's stored in InstructorTask:
    status['task_id'] = instructor_task.task_id
    status['task_state'] = instructor_task.task_state
    status['in_progress'] = instructor_task.task_state not in READY_STATES

#     if instructor_task.task_state in READY_STATES:
#         succeeded, message = get_task_completion_info(instructor_task)
#         status['message'] = message
#         status['succeeded'] = succeeded

    return status


def check_arguments_for_rescoring(course_id, problem_url):
    """
    Do simple checks on the descriptor to confirm that it supports rescoring.

    Confirms first that the problem_url is defined (since that's currently typed
    in).  An ItemNotFoundException is raised if the corresponding module
    descriptor doesn't exist.  NotImplementedError is raised if the
    corresponding module doesn't support rescoring calls.
    """
    descriptor = modulestore().get_instance(course_id, problem_url)
    if not hasattr(descriptor, 'module_class') or not hasattr(descriptor.module_class, 'rescore_problem'):
        msg = "Specified module does not support rescoring."
        raise NotImplementedError(msg)


def encode_problem_and_student_input(problem_url, student=None):
    """
    Encode problem_url and optional student into task_key and task_input values.

    `problem_url` is full URL of the problem.
    `student` is the user object of the student
    """
    if student is not None:
        task_input = {'problem_url': problem_url, 'student': student.username}
        task_key_stub = "{student}_{problem}".format(student=student.id, problem=problem_url)
    else:
        task_input = {'problem_url': problem_url}
        task_key_stub = "{student}_{problem}".format(student="", problem=problem_url)

    # create the key value by using MD5 hash:
    task_key = hashlib.md5(task_key_stub).hexdigest()

    return task_input, task_key


def submit_task(request, task_type, task_class, course_id, task_input, task_key):
    """
    Helper method to submit a task.

    Reserves the requested task, based on the `course_id`, `task_type`, and `task_key`,
    checking to see if the task is already running.  The `task_input` is also passed so that
    it can be stored in the resulting InstructorTask entry.  Arguments are extracted from
    the `request` provided by the originating server request.  Then the task is submitted to run
    asynchronously, using the specified `task_class`. Finally the InstructorTask entry is
    updated in order to store the task_id.

    `AlreadyRunningError` is raised if the task is already running.
    """
    # check to see if task is already running, and reserve it otherwise:
    instructor_task = _reserve_task(course_id, task_type, task_key, task_input, request.user)

    # submit task:
    task_args = [instructor_task.id, course_id, task_input, _get_xmodule_instance_args(request)]
    task_result = task_class.apply_async(task_args)

    # Update info in table with the resulting task_id (and state).
    _update_task(instructor_task, task_result)

    return instructor_task
