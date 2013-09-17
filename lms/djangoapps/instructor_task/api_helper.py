import hashlib
import json
import logging

from celery.result import AsyncResult
from celery.states import READY_STATES, SUCCESS, FAILURE, REVOKED

from courseware.module_render import get_xqueue_callback_url_prefix

from xmodule.modulestore.django import modulestore
from instructor_task.models import InstructorTask, PROGRESS


log = logging.getLogger(__name__)


class AlreadyRunningError(Exception):
    """Exception indicating that a background task is already running"""
    pass


def _task_is_running(course_id, task_type, task_key):
    """Checks if a particular task is already running"""
    runningTasks = InstructorTask.objects.filter(course_id=course_id, task_type=task_type, task_key=task_key)
    # exclude states that are "ready" (i.e. not "running", e.g. failure, success, revoked):
    for state in READY_STATES:
        runningTasks = runningTasks.exclude(task_state=state)
    return len(runningTasks) > 0


def _reserve_task(course_id, task_type, task_key, task_input, requester):
    """
    Creates a database entry to indicate that a task is in progress.

    Throws AlreadyRunningError if the task is already in progress.
    Includes the creation of an arbitrary value for task_id, to be
    submitted with the task call to celery.

    The InstructorTask.create method makes sure the InstructorTask entry is committed.
    When called from any view that is wrapped by TransactionMiddleware,
    and thus in a "commit-on-success" transaction, an autocommit buried within here
    will cause any pending transaction to be committed by a successful
    save here.  Any future database operations will take place in a
    separate transaction.

    Note that there is a chance of a race condition here, when two users
    try to run the same task at almost exactly the same time.  One user
    could be after the check and before the create when the second user
    gets to the check.  At that point, both users are able to run their
    tasks simultaneously.  This is deemed a small enough risk to not
    put in further safeguards.
    """

    if _task_is_running(course_id, task_type, task_key):
        raise AlreadyRunningError("requested task is already running")

    # Create log entry now, so that future requests will know it's running.
    return InstructorTask.create(course_id, task_type, task_key, task_input, requester)


def _get_xmodule_instance_args(request, task_id):
    """
    Calculate parameters needed for instantiating xmodule instances.

    The `request_info` will be passed to a tracking log function, to provide information
    about the source of the task request.   The `xqueue_callback_url_prefix` is used to
    permit old-style xqueue callbacks directly to the appropriate module in the LMS.
    The `task_id` is also passed to the tracking log function.
    """
    request_info = {'username': request.user.username,
                    'ip': request.META['REMOTE_ADDR'],
                    'agent': request.META.get('HTTP_USER_AGENT', ''),
                    'host': request.META['SERVER_NAME'],
                    }

    xmodule_instance_args = {'xqueue_callback_url_prefix': get_xqueue_callback_url_prefix(request),
                             'request_info': request_info,
                             'task_id': task_id,
                             }
    return xmodule_instance_args


def _update_instructor_task(instructor_task, task_result):
    """
    Updates and possibly saves a InstructorTask entry based on a task Result.

    Used when updated status is requested.

    The `instructor_task` that is passed in is updated in-place, but
    is usually not saved.  In general, tasks that have finished (either with
    success or failure) should have their entries updated by the task itself,
    so are not updated here.  Tasks that are still running are not updated
    while they run.  So the one exception to the no-save rule are tasks that
    are in a "revoked" state.  This may mean that the task never had the
    opportunity to update the InstructorTask entry.

    Calculates json to store in "task_output" field of the `instructor_task`,
    as well as updating the task_state.

    For a successful task, the json contains the output of the task result.
    For a failed task, the json contains "exception", "message", and "traceback"
    keys.   A revoked task just has a "message" stating it was revoked.
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
    task_output = None
    entry_needs_updating = True

    if result_state == SUCCESS and instructor_task.task_state == PROGRESS and len(instructor_task.subtasks) > 0:
        # This happens when running subtasks:  the result object is marked with SUCCESS,
        # meaning that the subtasks have successfully been defined.  However, the InstructorTask
        # will be marked as in PROGRESS, until the last subtask completes and marks it as SUCCESS.
        # We want to ignore the parent SUCCESS if subtasks are still running, and just trust the
        # contents of the InstructorTask.
        entry_needs_updating = False
    elif result_state in [PROGRESS, SUCCESS]:
        # construct a status message directly from the task result's result:
        # it needs to go back with the entry passed in.
        log.info("background task (%s), state %s:  result: %s", task_id, result_state, returned_result)
        task_output = InstructorTask.create_output_for_success(returned_result)
    elif result_state == FAILURE:
        # on failure, the result's result contains the exception that caused the failure
        exception = returned_result
        traceback = result_traceback if result_traceback is not None else ''
        log.warning("background task (%s) failed: %s %s", task_id, returned_result, traceback)
        task_output = InstructorTask.create_output_for_failure(exception, result_traceback)
    elif result_state == REVOKED:
        # on revocation, the result's result doesn't contain anything
        # but we cannot rely on the worker thread to set this status,
        # so we set it here.
        entry_needs_saving = True
        log.warning("background task (%s) revoked.", task_id)
        task_output = InstructorTask.create_output_for_revoked()

    # save progress and state into the entry, even if it's not being saved:
    # when celery is run in "ALWAYS_EAGER" mode, progress needs to go back
    # with the entry passed in.
    if entry_needs_updating:
        instructor_task.task_state = result_state
        if task_output is not None:
            instructor_task.task_output = task_output

        if entry_needs_saving:
            instructor_task.save()


def get_updated_instructor_task(task_id):
    """
    Returns InstructorTask object corresponding to a given `task_id`.

    If the InstructorTask thinks the task is still running, then
    the task's result is checked to return an updated state and output.
    """
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


def get_status_from_instructor_task(instructor_task):
    """
    Get the status for a given InstructorTask entry.

    Returns a dict, with the following keys:
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
    status = {}

    if instructor_task is not None:
        # status basic information matching what's stored in InstructorTask:
        status['task_id'] = instructor_task.task_id
        status['task_state'] = instructor_task.task_state
        status['in_progress'] = instructor_task.task_state not in READY_STATES
        if instructor_task.task_output is not None:
            status['task_progress'] = json.loads(instructor_task.task_output)

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
    Encode optional problem_url and optional student into task_key and task_input values.

    `problem_url` is full URL of the problem.
    `student` is the user object of the student
    """
    if student is not None:
        task_input = {'problem_url': problem_url, 'student': student.username}
        task_key_stub = "{student}_{problem}".format(student=student.id, problem=problem_url)
    else:
        task_input = {'problem_url': problem_url}
        task_key_stub = "_{problem}".format(problem=problem_url)

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
    asynchronously, using the specified `task_class` and using the task_id constructed for it.

    `AlreadyRunningError` is raised if the task is already running.

    The _reserve_task method makes sure the InstructorTask entry is committed.
    When called from any view that is wrapped by TransactionMiddleware,
    and thus in a "commit-on-success" transaction, an autocommit buried within here
    will cause any pending transaction to be committed by a successful
    save here.  Any future database operations will take place in a
    separate transaction.

    """
    # check to see if task is already running, and reserve it otherwise:
    instructor_task = _reserve_task(course_id, task_type, task_key, task_input, request.user)

    # submit task:
    task_id = instructor_task.task_id
    task_args = [instructor_task.id, _get_xmodule_instance_args(request, task_id)]
    task_class.apply_async(task_args, task_id=task_id)

    return instructor_task