
import json
from time import time
from sys import exc_info
from traceback import format_exc

from django.contrib.auth.models import User
from django.db import transaction
from celery import task, current_task
from celery.utils.log import get_task_logger

from xmodule.modulestore.django import modulestore

import mitxmako.middleware as middleware
from track.views import task_track

from courseware.models import StudentModule, CourseTaskLog
from courseware.model_data import ModelDataCache
from courseware.module_render import get_module_for_descriptor_internal


# define different loggers for use within tasks and on client side
task_log = get_task_logger(__name__)


class UpdateProblemModuleStateError(Exception):
    """
    Error signaling a fatal condition while updating problem modules.

    Used when the current module cannot be processed and that no more
    modules should be attempted.
    """
    pass


def _update_problem_module_state_internal(course_id, module_state_key, student_identifier, update_fcn, action_name, filter_fcn,
                                          xmodule_instance_args):
    """
    Performs generic update by visiting StudentModule instances with the update_fcn provided.

    StudentModule instances are those that match the specified `course_id` and `module_state_key`.
    If `student_identifier` is not None, it is used as an additional filter to limit the modules to those belonging
    to that student. If `student_identifier` is None, performs update on modules for all students on the specified problem.

    If a `filter_fcn` is not None, it is applied to the query that has been constructed.  It takes one
    argument, which is the query being filtered.

    The `update_fcn` is called on each StudentModule that passes the resulting filtering.
    It is passed three arguments:  the module_descriptor for the module pointed to by the
    module_state_key, the particular StudentModule to update, and the xmodule_instance_args being
    passed through.

    Because this is run internal to a task, it does not catch exceptions.  These are allowed to pass up to the
    next level, so that it can set the failure modes and capture the error trace in the CourseTaskLog and the
    result object.
    """
    # get start time for task:
    start_time = time()

    # Hack to get mako templates to work on celery worker server's worker thread.
    # The initialization of Mako templating is usually done when Django is
    # initializing middleware packages as part of processing a server request.
    # When this is run on a celery worker server, no such initialization is
    # called. Using @worker_ready.connect doesn't run in the right container.
    #  So we look for the result: the defining of the lookup paths
    # for templates.
    if 'main' not in middleware.lookup:
        task_log.info("Initializing Mako middleware explicitly")
        middleware.MakoMiddleware()

    # find the problem descriptor:
    module_descriptor = modulestore().get_instance(course_id, module_state_key)

    # find the module in question
    modules_to_update = StudentModule.objects.filter(course_id=course_id,
                                                     module_state_key=module_state_key)

    # give the option of rescoring an individual student. If not specified,
    # then rescores all students who have responded to a problem so far
    student = None
    if student_identifier is not None:
        # if an identifier is supplied, then look for the student,
        # and let it throw an exception if none is found.
        if "@" in student_identifier:
            student = User.objects.get(email=student_identifier)
        elif student_identifier is not None:
            student = User.objects.get(username=student_identifier)

    if student is not None:
        modules_to_update = modules_to_update.filter(student_id=student.id)

    if filter_fcn is not None:
        modules_to_update = filter_fcn(modules_to_update)

    # perform the main loop
    num_updated = 0
    num_attempted = 0
    num_total = modules_to_update.count()

    def get_task_progress():
        """Return a dict containing info about current task"""
        current_time = time()
        progress = {'action_name': action_name,
                    'attempted': num_attempted,
                    'updated': num_updated,
                    'total': num_total,
                    'start_ms': int(start_time * 1000),
                    'duration_ms': int((current_time - start_time) * 1000),
                    }
        return progress

    for module_to_update in modules_to_update:
        num_attempted += 1
        # There is no try here:  if there's an error, we let it throw, and the task will
        # be marked as FAILED, with a stack trace.
        if update_fcn(module_descriptor, module_to_update, xmodule_instance_args):
            # If the update_fcn returns true, then it performed some kind of work.
            num_updated += 1

        # update task status:
        current_task.update_state(state='PROGRESS', meta=get_task_progress())

    task_progress = get_task_progress()
    # update progress without updating the state
    current_task.update_state(state='PROGRESS', meta=task_progress)
    return task_progress


@transaction.autocommit
def _save_course_task_log_entry(entry):
    """Writes CourseTaskLog entry immediately."""
    entry.save()


def _update_problem_module_state(entry_id, course_id, module_state_key, student_ident, update_fcn, action_name, filter_fcn,
                                 xmodule_instance_args):
    """
    Performs generic update by visiting StudentModule instances with the update_fcn provided.

    See _update_problem_module_state_internal function for more details on arguments.

    The `entry_id` is the primary key for the CourseTaskLog entry representing the task.  This function
    updates the entry on SUCCESS and FAILURE of the _update_problem_module_state_internal function it
    wraps.

    Once exceptions are caught and recorded in the CourseTaskLog entry, they are allowed to pass up to the
    task-running level, so that it can also set the failure modes and capture the error trace in the result object.
    """
    task_id = current_task.request.id
    fmt = 'Starting to update problem modules as task "{task_id}": course "{course_id}" problem "{state_key}": nothing {action} yet'
    task_log.info(fmt.format(task_id=task_id, course_id=course_id, state_key=module_state_key, action=action_name))

    # get the CourseTaskLog to be updated.  If this fails, then let the exception return to Celery.
    # There's no point in catching it here.
    entry = CourseTaskLog.objects.get(pk=entry_id)
    entry.task_id = task_id
    _save_course_task_log_entry(entry)

    # add task_id to xmodule_instance_args, so that it can be output with tracking info:
    xmodule_instance_args['task_id'] = task_id

    # now that we have an entry we can try to catch failures:
    task_progress = None
    try:
        task_progress = _update_problem_module_state_internal(course_id, module_state_key, student_ident, update_fcn,
                                                              action_name, filter_fcn, xmodule_instance_args)
    except Exception:
        # try to write out the failure to the entry before failing
        exception_type, exception, traceback = exc_info()
        traceback_string = format_exc(traceback) if traceback is not None else ''
        task_progress = {'exception': exception_type.__name__, 'message': str(exception.message)}
        task_log.warning("background task (%s) failed: %s %s", task_id, exception, traceback_string)
        if traceback is not None:
            task_progress['traceback'] = traceback_string
        entry.task_output = json.dumps(task_progress)
        entry.task_state = 'FAILURE'
        _save_course_task_log_entry(entry)
        raise

    # if we get here, we assume we've succeeded, so update the CourseTaskLog entry in anticipation:
    entry.task_output = json.dumps(task_progress)
    entry.task_state = 'SUCCESS'
    _save_course_task_log_entry(entry)

    # log and exit, returning task_progress info as task result:
    fmt = 'Finishing task "{task_id}": course "{course_id}" problem "{state_key}": final: {progress}'
    task_log.info(fmt.format(task_id=task_id, course_id=course_id, state_key=module_state_key, progress=task_progress))
    return task_progress


def _update_problem_module_state_for_student(entry_id, course_id, problem_url, student_identifier,
                                             update_fcn, action_name, filter_fcn=None, xmodule_instance_args=None):
    """
    Update the StudentModule for a given student.  See _update_problem_module_state().
    """
    msg = ''
    success = False
    # try to uniquely id student by email address or username
    try:
        if "@" in student_identifier:
            student_to_update = User.objects.get(email=student_identifier)
        elif student_identifier is not None:
            student_to_update = User.objects.get(username=student_identifier)
        return _update_problem_module_state(entry_id, course_id, problem_url, student_to_update, update_fcn,
                                            action_name, filter_fcn, xmodule_instance_args)
    except User.DoesNotExist:
        msg = "Couldn't find student with that email or username."

    return (success, msg)


def _get_module_instance_for_task(course_id, student, module_descriptor, module_state_key, xmodule_instance_args=None,
                                  grade_bucket_type=None):
    """
    Fetches a StudentModule instance for a given course_id, student, and module_state_key.

    Includes providing information for creating a track function and an XQueue callback,
    but does not require passing in a Request object.
    """
    # reconstitute the problem's corresponding XModule:
    model_data_cache = ModelDataCache.cache_for_descriptor_descendents(course_id, student, module_descriptor)

    # get request-related tracking information from args passthrough, and supplement with task-specific
    # information:
    request_info = xmodule_instance_args.get('request_info', {}) if xmodule_instance_args is not None else {}
    task_info = {"student": student.username, "task_id": xmodule_instance_args['task_id']}

    def make_track_function():
        '''
        Make a tracking function that logs what happened.
        For insertion into ModuleSystem, and use by CapaModule.
        '''
        def f(event_type, event):
            return task_track(request_info, task_info, event_type, event, page='x_module_task')
        return f

    xqueue_callback_url_prefix = ''
    if xmodule_instance_args is not None:
        xqueue_callback_url_prefix = xmodule_instance_args.get('xqueue_callback_url_prefix')

    return get_module_for_descriptor_internal(student, module_descriptor, model_data_cache, course_id,
                                              make_track_function(), xqueue_callback_url_prefix,
                                              grade_bucket_type=grade_bucket_type)


@transaction.autocommit
def _rescore_problem_module_state(module_descriptor, student_module, xmodule_instance_args=None):
    '''
    Takes an XModule descriptor and a corresponding StudentModule object, and
    performs rescoring on the student's problem submission.

    Throws exceptions if the rescoring is fatal and should be aborted if in a loop.
    '''
    # unpack the StudentModule:
    course_id = student_module.course_id
    student = student_module.student
    module_state_key = student_module.module_state_key

    instance = _get_module_instance_for_task(course_id, student, module_descriptor, module_state_key, xmodule_instance_args, grade_bucket_type='rescore')

    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        msg = "No module {loc} for student {student}--access denied?".format(loc=module_state_key,
                                                                             student=student)
        task_log.debug(msg)
        raise UpdateProblemModuleStateError(msg)

    if not hasattr(instance, 'rescore_problem'):
        # if the first instance doesn't have a rescore method, we should
        # probably assume that no other instances will either.
        msg = "Specified problem does not support rescoring."
        raise UpdateProblemModuleStateError(msg)

    result = instance.rescore_problem()
    if 'success' not in result:
        # don't consider these fatal, but false means that the individual call didn't complete:
        task_log.warning("error processing rescore call for problem {loc} and student {student}: "
                 "unexpected response {msg}".format(msg=result, loc=module_state_key, student=student))
        return False
    elif result['success'] != 'correct' and result['success'] != 'incorrect':
        task_log.warning("error processing rescore call for problem {loc} and student {student}: "
                  "{msg}".format(msg=result['success'], loc=module_state_key, student=student))
        return False
    else:
        task_log.debug("successfully processed rescore call for problem {loc} and student {student}: "
                  "{msg}".format(msg=result['success'], loc=module_state_key, student=student))
        return True


def filter_problem_module_state_for_done(modules_to_update):
    """Filter to apply for rescoring, to limit module instances to those marked as done"""
    return modules_to_update.filter(state__contains='"done": true')


@task
def rescore_problem(entry_id, course_id, task_input, xmodule_instance_args):
    """Rescores problem `problem_url` in `course_id` for all students."""
    action_name = 'rescored'
    update_fcn = _rescore_problem_module_state
    filter_fcn = filter_problem_module_state_for_done
    problem_url = task_input.get('problem_url')
    student_ident = None
    if 'student' in task_input:
        student_ident = task_input['student']
    return _update_problem_module_state(entry_id, course_id, problem_url, student_ident,
                                        update_fcn, action_name, filter_fcn=filter_fcn,
                                        xmodule_instance_args=xmodule_instance_args)


@transaction.autocommit
def _reset_problem_attempts_module_state(module_descriptor, student_module, xmodule_instance_args=None):
    """
    Resets problem attempts to zero for specified `student_module`.

    Always returns true, if it doesn't throw an exception.
    """
    problem_state = json.loads(student_module.state)
    if 'attempts' in problem_state:
        old_number_of_attempts = problem_state["attempts"]
        if old_number_of_attempts > 0:
            problem_state["attempts"] = 0
            # convert back to json and save
            student_module.state = json.dumps(problem_state)
            student_module.save()
            # get request-related tracking information from args passthrough,
            # and supplement with task-specific information:
            request_info = xmodule_instance_args.get('request_info', {}) if xmodule_instance_args is not None else {}
            task_id = xmodule_instance_args['task_id'] if xmodule_instance_args is not None else "unknown-task_id"
            task_info = {"student": student_module.student.username, "task_id": task_id}
            event_info = {"old_attempts": old_number_of_attempts, "new_attempts": 0}
            task_track(request_info, task_info, 'problem_reset_attempts', event_info, page='x_module_task')

    # consider the reset to be successful, even if no update was performed.  (It's just "optimized".)
    return True


@task
def reset_problem_attempts(entry_id, course_id, task_input, xmodule_instance_args):
    """Resets problem attempts to zero for `problem_url` in `course_id` for all students."""
    action_name = 'reset'
    update_fcn = _reset_problem_attempts_module_state
    problem_url = task_input.get('problem_url')
    student_ident = None
    if 'student' in task_input:
        student_ident = task_input['student']
    return _update_problem_module_state(entry_id, course_id, problem_url, student_ident,
                                        update_fcn, action_name, filter_fcn=None,
                                        xmodule_instance_args=xmodule_instance_args)


@transaction.autocommit
def _delete_problem_module_state(module_descriptor, student_module, xmodule_instance_args=None):
    """Delete the StudentModule entry."""
    student_module.delete()
    # get request-related tracking information from args passthrough,
    # and supplement with task-specific information:
    request_info = xmodule_instance_args.get('request_info', {}) if xmodule_instance_args is not None else {}
    task_id = xmodule_instance_args['task_id'] if xmodule_instance_args is not None else "unknown-task_id"
    task_info = {"student": student_module.student.username, "task_id": task_id}
    task_track(request_info, task_info, 'problem_delete_state', {}, page='x_module_task')
    return True


@task
def delete_problem_state(entry_id, course_id, task_input, xmodule_instance_args):
    """Deletes problem state entirely for `problem_url` in `course_id` for all students."""
    action_name = 'deleted'
    update_fcn = _delete_problem_module_state
    problem_url = task_input.get('problem_url')
    student_ident = None
    if 'student' in task_input:
        student_ident = task_input['student']
    return _update_problem_module_state(entry_id, course_id, problem_url, student_ident,
                                        update_fcn, action_name, filter_fcn=None,
                                        xmodule_instance_args=xmodule_instance_args)
