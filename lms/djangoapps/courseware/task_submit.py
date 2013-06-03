import hashlib
import json
import logging
from django.http import HttpResponse
from django.db import transaction

from celery.result import AsyncResult
from celery.states import READY_STATES, SUCCESS, FAILURE, REVOKED

from courseware.models import CourseTask
from courseware.module_render import get_xqueue_callback_url_prefix
from courseware.tasks import (PROGRESS, rescore_problem,
                              reset_problem_attempts, delete_problem_state)
from xmodule.modulestore.django import modulestore


log = logging.getLogger(__name__)

# define a "state" used in CourseTask
QUEUING = 'QUEUING'

class AlreadyRunningError(Exception):
    pass


def get_running_course_tasks(course_id):
    """
    Returns a query of CourseTask objects of running tasks for a given course.

    Used to generate a list of tasks to display on the instructor dashboard.
    """
    course_tasks = CourseTask.objects.filter(course_id=course_id)
    # exclude states that are "ready" (i.e. not "running", e.g. failure, success, revoked):
    for state in READY_STATES:
        course_tasks = course_tasks.exclude(task_state=state)
    return course_tasks


def get_course_task_history(course_id, problem_url, student=None):
    """
    Returns a query of CourseTask objects of historical tasks for a given course,
    that match a particular problem and optionally a student.
    """
    _, task_key = _encode_problem_and_student_input(problem_url, student)

    course_tasks = CourseTask.objects.filter(course_id=course_id, task_key=task_key)
    return course_tasks.order_by('-id')


def course_task_status(request):
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
    output = {}
    if 'task_id' in request.REQUEST:
        task_id = request.REQUEST['task_id']
        output = _get_course_task_status(task_id)
    elif 'task_ids[]' in request.REQUEST:
        tasks = request.REQUEST.getlist('task_ids[]')
        for task_id in tasks:
            task_output = _get_course_task_status(task_id)
            if task_output is not None:
                output[task_id] = task_output

    return HttpResponse(json.dumps(output, indent=4))


def _task_is_running(course_id, task_type, task_key):
    """Checks if a particular task is already running"""
    runningTasks = CourseTask.objects.filter(course_id=course_id, task_type=task_type, task_key=task_key)
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

    course_task = CourseTask.objects.create(**tasklog_args)
    return course_task


@transaction.autocommit
def _update_task(course_task, task_result):
    """
    Updates a database entry with information about the submitted task.

    Autocommit annotation makes sure the database entry is committed.
    """
    # we at least update the entry with the task_id, and for ALWAYS_EAGER mode,
    # we update other status as well.  (For non-ALWAYS_EAGER modes, the entry
    # should not have changed except for setting PENDING state and the
    # addition of the task_id.)
    _update_course_task(course_task, task_result)
    course_task.save()


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


def _update_course_task(course_task, task_result):
    """
    Updates and possibly saves a CourseTask entry based on a task Result.

    Used when a task initially returns, as well as when updated status is
    requested.

    The `course_task` that is passed in is updated in-place, but
    is usually not saved.  In general, tasks that have finished (either with
    success or failure) should have their entries updated by the task itself,
    so are not updated here.  Tasks that are still running are not updated
    while they run.  So the one exception to the no-save rule are tasks that
    are in a "revoked" state.  This may mean that the task never had the
    opportunity to update the CourseTask entry.

    Calculates json to store in "task_output" field of the `course_task`,
    as well as updating the task_state and task_id (which may not yet be set
    if this is the first call after the task is submitted).

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

    # Assume we don't always update the CourseTask entry if we don't have to:
    entry_needs_saving = False
    output = {}

    if result_state == PROGRESS:
        # construct a status message directly from the task result's result:
        # it needs to go back with the entry passed in.
        course_task.task_output = json.dumps(returned_result)
        output['task_progress'] = returned_result
        log.info("background task (%s), succeeded: %s", task_id, returned_result)

    elif result_state == FAILURE:
        # on failure, the result's result contains the exception that caused the failure
        exception = returned_result
        traceback = result_traceback if result_traceback is not None else ''
        task_progress = {'exception': type(exception).__name__, 'message': str(exception.message)}
        output['message'] = exception.message
        log.warning("background task (%s) failed: %s %s", task_id, returned_result, traceback)
        if result_traceback is not None:
            output['task_traceback'] = result_traceback
            # truncate any traceback that goes into the CourseTask model:
            task_progress['traceback'] = result_traceback[:700]
        # save progress into the entry, even if it's not being saved:
        # when celery is run in "ALWAYS_EAGER" mode, progress needs to go back 
        # with the entry passed in.
        course_task.task_output = json.dumps(task_progress)
        output['task_progress'] = task_progress

    elif result_state == REVOKED:
        # on revocation, the result's result doesn't contain anything
        # but we cannot rely on the worker thread to set this status,
        # so we set it here.
        entry_needs_saving = True
        message = 'Task revoked before running'
        output['message'] = message
        log.warning("background task (%s) revoked.", task_id)
        task_progress = {'message': message}
        course_task.task_output = json.dumps(task_progress)
        output['task_progress'] = task_progress

    # Always update the local version of the entry if the state has changed.
    # This is important for getting the task_id into the initial version
    # of the course_task, and also for development environments
    # when this code is executed when celery is run in "ALWAYS_EAGER" mode.
    if result_state != course_task.task_state:
        course_task.task_state = result_state
        course_task.task_id = task_id

    if entry_needs_saving:
        course_task.save()

    return output


def _get_course_task_status(task_id):
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

      If task has been REVOKED, the CourseTask entry will be updated.
    """
    # First check if the task_id is known
    try:
        course_task = CourseTask.objects.get(task_id=task_id)
    except CourseTask.DoesNotExist:
        log.warning("query for CourseTask status failed: task_id=(%s) not found", task_id)
        return None

    status = {}

    # if the task is not already known to be done, then we need to query
    # the underlying task's result object:
    if course_task.task_state not in READY_STATES:
        result = AsyncResult(task_id)
        status.update(_update_course_task(course_task, result))
    elif course_task.task_output is not None:
        # task is already known to have finished, but report on its status:
        status['task_progress'] = json.loads(course_task.task_output)

    # status basic information matching what's stored in CourseTask:
    status['task_id'] = course_task.task_id
    status['task_state'] = course_task.task_state
    status['in_progress'] = course_task.task_state not in READY_STATES

    if course_task.task_state in READY_STATES:
        succeeded, message = get_task_completion_info(course_task)
        status['message'] = message
        status['succeeded'] = succeeded

    return status


def get_task_completion_info(course_task):
    """
    Construct progress message from progress information in CourseTask entry.

    Returns (boolean, message string) duple, where the boolean indicates
    whether the task completed without incident.  (It is possible for a
    task to attempt many sub-tasks, such as rescoring many students' problem
    responses, and while the task runs to completion, some of the students'
    responses could not be rescored.)

    Used for providing messages to course_task_status(), as well as
    external calls for providing course task submission history information.
    """
    succeeded = False

    if course_task.task_output is None:
        log.warning("No task_output information found for course_task {0}".format(course_task.task_id))
        return (succeeded, "No status information available")

    task_output = json.loads(course_task.task_output)
    if course_task.task_state in [FAILURE, REVOKED]:
        return(succeeded, task_output['message'])

    action_name = task_output['action_name']
    num_attempted = task_output['attempted']
    num_updated = task_output['updated']
    num_total = task_output['total']

    if course_task.task_input is None:
        log.warning("No task_input information found for course_task {0}".format(course_task.task_id))
        return (succeeded, "No status information available")
    task_input = json.loads(course_task.task_input)
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


def _check_arguments_for_rescoring(course_id, problem_url):
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


def _encode_problem_and_student_input(problem_url, student=None):
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


def _submit_task(request, task_type, task_class, course_id, task_input, task_key):
    """
    Helper method to submit a task.

    Reserves the requested task, based on the `course_id`, `task_type`, and `task_key`,
    checking to see if the task is already running.  The `task_input` is also passed so that
    it can be stored in the resulting CourseTask entry.  Arguments are extracted from
    the `request` provided by the originating server request.  Then the task is submitted to run
    asynchronously, using the specified `task_class`. Finally the CourseTask entry is
    updated in order to store the task_id.

    `AlreadyRunningError` is raised if the task is already running.
    """
    # check to see if task is already running, and reserve it otherwise:
    course_task = _reserve_task(course_id, task_type, task_key, task_input, request.user)

    # submit task:
    task_args = [course_task.id, course_id, task_input, _get_xmodule_instance_args(request)]
    task_result = task_class.apply_async(task_args)

    # Update info in table with the resulting task_id (and state).
    _update_task(course_task, task_result)

    return course_task


def submit_rescore_problem_for_student(request, course_id, problem_url, student):
    """
    Request a problem to be rescored as a background task.

    The problem will be rescored for the specified student only.  Parameters are the `course_id`,
    the `problem_url`, and the `student` as a User object.
    The url must specify the location of the problem, using i4x-type notation.

    ItemNotFoundException is raised if the problem doesn't exist, or AlreadyRunningError
    if the problem is already being rescored for this student, or NotImplementedError if
    the problem doesn't support rescoring.
    """
    # check arguments:  let exceptions return up to the caller.
    _check_arguments_for_rescoring(course_id, problem_url)

    task_type = 'rescore_problem'
    task_class = rescore_problem
    task_input, task_key = _encode_problem_and_student_input(problem_url, student)
    return _submit_task(request, task_type, task_class, course_id, task_input, task_key)


def submit_rescore_problem_for_all_students(request, course_id, problem_url):
    """
    Request a problem to be rescored as a background task.

    The problem will be rescored for all students who have accessed the
    particular problem in a course and have provided and checked an answer.
    Parameters are the `course_id` and the `problem_url`.
    The url must specify the location of the problem, using i4x-type notation.

    ItemNotFoundException is raised if the problem doesn't exist, or AlreadyRunningError
    if the problem is already being rescored, or NotImplementedError if the problem doesn't
    support rescoring.
    """
    # check arguments:  let exceptions return up to the caller.
    _check_arguments_for_rescoring(course_id, problem_url)

    # check to see if task is already running, and reserve it otherwise
    task_type = 'rescore_problem'
    task_class = rescore_problem
    task_input, task_key = _encode_problem_and_student_input(problem_url)
    return _submit_task(request, task_type, task_class, course_id, task_input, task_key)


def submit_reset_problem_attempts_for_all_students(request, course_id, problem_url):
    """
    Request to have attempts reset for a problem as a background task.

    The problem's attempts will be reset for all students who have accessed the
    particular problem in a course.  Parameters are the `course_id` and
    the `problem_url`.  The url must specify the location of the problem,
    using i4x-type notation.

    ItemNotFoundException is raised if the problem doesn't exist, or AlreadyRunningError
    if the problem is already being reset.
    """
    # check arguments:  make sure that the problem_url is defined
    # (since that's currently typed in).  If the corresponding module descriptor doesn't exist,
    # an exception will be raised.  Let it pass up to the caller.
    modulestore().get_instance(course_id, problem_url)

    task_type = 'reset_problem_attempts'
    task_class = reset_problem_attempts
    task_input, task_key = _encode_problem_and_student_input(problem_url)
    return _submit_task(request, task_type, task_class, course_id, task_input, task_key)


def submit_delete_problem_state_for_all_students(request, course_id, problem_url):
    """
    Request to have state deleted for a problem as a background task.

    The problem's state will be deleted for all students who have accessed the
    particular problem in a course.  Parameters are the `course_id` and
    the `problem_url`.  The url must specify the location of the problem,
    using i4x-type notation.

    ItemNotFoundException is raised if the problem doesn't exist, or AlreadyRunningError
    if the particular problem is already being deleted.
    """
    # check arguments:  make sure that the problem_url is defined
    # (since that's currently typed in).  If the corresponding module descriptor doesn't exist,
    # an exception will be raised.  Let it pass up to the caller.
    modulestore().get_instance(course_id, problem_url)

    task_type = 'delete_problem_state'
    task_class = delete_problem_state
    task_input, task_key = _encode_problem_and_student_input(problem_url)
    return _submit_task(request, task_type, task_class, course_id, task_input, task_key)
