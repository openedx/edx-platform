
import json
import logging
from django.contrib.auth.models import User
from courseware.models import StudentModule, CourseTaskLog
from courseware.model_data import ModelDataCache
from courseware.module_render import get_module

from xmodule.modulestore.django import modulestore
from xmodule.modulestore.exceptions import ItemNotFoundError,\
    InvalidLocationError
import track.views

from celery import task, current_task
from celery.utils.log import get_task_logger
from time import sleep
from django.core.handlers.wsgi import WSGIRequest

logger = get_task_logger(__name__)

# celery = Celery('tasks', broker='django://')

log = logging.getLogger(__name__)


@task
def add(x, y):
    return x + y


@task
def echo(value):
    if value == 'ping':
        result = 'pong'
    else:
        result = 'got: {0}'.format(value)

    return result


@task
def waitawhile(value):
    for i in range(value):
        sleep(1)  # in seconds
        logger.info('Waited {0} seconds...'.format(i))
        current_task.update_state(state='PROGRESS',
                                  meta={'current': i, 'total': value})

    result = 'Yeah!'
    return result


class UpdateProblemModuleStateError(Exception):
    pass


def _update_problem_module_state(request, course_id, problem_url, student, update_fcn, action_name, filter_fcn):
    '''
    Performs generic update by visiting StudentModule instances with the update_fcn provided

    If student is None, performs update on modules for all students on the specified problem
    '''
    module_state_key = problem_url
    # TODO: store this in the task state, not as a separate return value.
    # (Unless that's not what the task state is intended to mean.  The task can successfully
    # complete, as far as celery is concerned, but have an internal status of failed.)
    succeeded = False

    # find the problem descriptor, if any:
    try:
        module_descriptor = modulestore().get_instance(course_id, module_state_key)
        succeeded = True
    except ItemNotFoundError:
        msg = "Couldn't find problem with that urlname."
    except InvalidLocationError:
        msg = "Couldn't find problem with that urlname."
    if module_descriptor is None:
        msg = "Couldn't find problem with that urlname."
#    if not succeeded:
#        current_task.update_state(
#                                  meta={'attempted': num_attempted, 'updated': num_updated, 'total': num_total})
# The task should still succeed, but should have metadata indicating
# that the result of the successful task was a failure.  (It's not
# the queue that failed, but the task put on the queue.)

    # find the module in question
    succeeded = False
    modules_to_update = StudentModule.objects.filter(course_id=course_id,
                                                     module_state_key=module_state_key)

    # give the option of regrading an individual student. If not specified,
    # then regrades all students who have responded to a problem so far
    if student is not None:
        modules_to_update = modules_to_update.filter(student_id=student.id)

    if filter_fcn is not None:
        modules_to_update = filter_fcn(modules_to_update)

    # perform the main loop
    num_updated = 0
    num_attempted = 0
    num_total = len(modules_to_update)  # TODO: make this more efficient.  Count()?
    for module_to_update in modules_to_update:
        num_attempted += 1
#        try:
        if update_fcn(request, module_to_update, module_descriptor):
            num_updated += 1
# if there's an error, just let it throw, and the task will 
# be marked as FAILED, with a stack trace.            
#        except UpdateProblemModuleStateError as e:
            # something bad happened, so exit right away
#            return (succeeded, e.message)
        # update task status:
        current_task.update_state(state='PROGRESS',
                                  meta={'attempted': num_attempted, 'updated': num_updated, 'total': num_total})

    # done with looping through all modules, so just return final statistics:
    if student is not None:
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

    msg = msg.format(action=action_name, updated=num_updated, attempted=num_attempted, student=student, problem=module_state_key)
    # update status in task result object itself:
    current_task.update_state(state='DONE',
                              meta={'attempted': num_attempted, 'updated': num_updated, 'total': num_total,
                                    'succeeded': succeeded, 'message': msg})

    # and update status in course task table as well:
    # TODO: figure out how this is legal.  The actual task result
    # status is updated by celery when this task completes, and is
    # not
#    course_task_log_entry = CourseTaskLog.objects.get(task_id=current_task.id)
#    course_task_log_entry.task_status = ...

    # return (succeeded, msg)
    return succeeded


def _update_problem_module_state_for_student(request, course_id, problem_url, student_identifier,
                                             update_fcn, action_name, filter_fcn=None):
    msg = ''
    success = False
    # try to uniquely id student by email address or username
    try:
        if "@" in student_identifier:
            student_to_update = User.objects.get(email=student_identifier)
        elif student_identifier is not None:
            student_to_update = User.objects.get(username=student_identifier)
        return _update_problem_module_state(request, course_id, problem_url, student_to_update, update_fcn, action_name, filter_fcn)
    except User.DoesNotExist:
        msg = "Couldn't find student with that email or username."

    return (success, msg)


def _update_problem_module_state_for_all_students(request, course_id, problem_url, update_fcn, action_name, filter_fcn=None):
    return _update_problem_module_state(request, course_id, problem_url, None, update_fcn, action_name, filter_fcn)


def _regrade_problem_module_state(request, module_to_regrade, module_descriptor):
    '''
    Takes an XModule descriptor and a corresponding StudentModule object, and
    performs regrading on the student's problem submission.

    Throws exceptions if the regrading is fatal and should be aborted if in a loop.
    '''
    # unpack the StudentModule:
    course_id = module_to_regrade.course_id
    student = module_to_regrade.student
    module_state_key = module_to_regrade.module_state_key

    # reconstitute the problem's corresponding XModule:
    model_data_cache = ModelDataCache.cache_for_descriptor_descendents(course_id, student,
                                                                       module_descriptor)
    # Note that the request is passed to get_module() to provide xqueue-related URL information
    instance = get_module(student, request, module_state_key, model_data_cache,
                          course_id, grade_bucket_type='regrade')

    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        msg = "No module {loc} for student {student}--access denied?".format(loc=module_state_key,
                                                                             student=student)
        log.debug(msg)
        raise UpdateProblemModuleStateError(msg)

    if not hasattr(instance, 'regrade_problem'):
        # if the first instance doesn't have a regrade method, we should
        # probably assume that no other instances will either.
        msg = "Specified problem does not support regrading."
        raise UpdateProblemModuleStateError(msg)

    result = instance.regrade_problem()
    if 'success' not in result:
        # don't consider these fatal, but false means that the individual call didn't complete:
        log.debug("error processing regrade call for problem {loc} and student {student}: "
                 "unexpected response {msg}".format(msg=result, loc=module_state_key, student=student))
        return False
    elif result['success'] != 'correct' and result['success'] != 'incorrect':
        log.debug("error processing regrade call for problem {loc} and student {student}: "
                  "{msg}".format(msg=result['success'], loc=module_state_key, student=student))
        return False
    else:
        track.views.server_track(request,
                                 '{instructor} regrade problem {problem} for student {student} '
                                 'in {course}'.format(student=student.id,
                                                      problem=module_to_regrade.module_state_key,
                                                      instructor=request.user,
                                                      course=course_id),
                                 {},
                                 page='idashboard')
        return True


def filter_problem_module_state_for_done(modules_to_update):
    return modules_to_update.filter(state__contains='"done": true')


@task
def _regrade_problem_for_student(request, course_id, problem_url, student_identifier):
    action_name = 'regraded'
    update_fcn = _regrade_problem_module_state
    filter_fcn = filter_problem_module_state_for_done
    return _update_problem_module_state_for_student(request, course_id, problem_url, student_identifier,
                                                    update_fcn, action_name, filter_fcn)


def regrade_problem_for_student(request, course_id, problem_url, student_identifier):
    # First submit task.  Then  put stuff into table with the resulting task_id.
    result = _regrade_problem_for_student.apply_async(request, course_id, problem_url, student_identifier)
    task_id = result.id
    # TODO: for log, would want student_identifier to already be mapped to the student
    tasklog_args = {'course_id': course_id,
                    'task_name': 'regrade',
                    'task_args': problem_url,
                    'task_id': task_id,
                    'task_status': result.state,
                    'requester': request.user}

    CourseTaskLog.objects.create(**tasklog_args)
    return result


@task
def _regrade_problem_for_all_students(request_environ, course_id, problem_url):
#    request = dummy_request
    request = WSGIRequest(request_environ)
    action_name = 'regraded'
    update_fcn = _regrade_problem_module_state
    filter_fcn = filter_problem_module_state_for_done
    return _update_problem_module_state_for_all_students(request, course_id, problem_url,
                                                         update_fcn, action_name, filter_fcn)


def regrade_problem_for_all_students(request, course_id, problem_url):
    # Figure out (for now) how to serialize what we need of the request.  The actual
    # request will not successfully serialize with json or with pickle.
    request_environ = {'HTTP_USER_AGENT': request.META['HTTP_USER_AGENT'],
                       'REMOTE_ADDR': request.META['REMOTE_ADDR'],
                       'SERVER_NAME': request.META['SERVER_NAME'],
                       'REQUEST_METHOD': 'GET',
#                             'HTTP_X_FORWARDED_PROTO': request.META['HTTP_X_FORWARDED_PROTO'],
                      }

    # Submit task.  Then put stuff into table with the resulting task_id.
    task_args = [request_environ, course_id, problem_url]
    result = _regrade_problem_for_all_students.apply_async(task_args)
    task_id = result.id
    tasklog_args = {'course_id': course_id,
                    'task_name': 'regrade',
                    'task_args': problem_url,
                    'task_id': task_id,
                    'task_status': result.state,
                    'requester': request.user}
    course_task_log = CourseTaskLog.objects.create(**tasklog_args)
    return course_task_log


def _reset_problem_attempts_module_state(request, module_to_reset, module_descriptor):
    # modify the problem's state
    # load the state json and change state
    problem_state = json.loads(module_to_reset.state)
    if 'attempts' in problem_state:
        old_number_of_attempts = problem_state["attempts"]
        if old_number_of_attempts > 0:
            problem_state["attempts"] = 0
            # convert back to json and save
            module_to_reset.state = json.dumps(problem_state)
            module_to_reset.save()
            # write out tracking info
            track.views.server_track(request,
                                     '{instructor} reset attempts from {old_attempts} to 0 for {student} '
                                     'on problem {problem} in {course}'.format(old_attempts=old_number_of_attempts,
                                                                               student=module_to_reset.student,
                                                                               problem=module_to_reset.module_state_key,
                                                                               instructor=request.user,
                                                                               course=module_to_reset.course_id),
                                     {},
                                     page='idashboard')

    # consider the reset to be successful, even if no update was performed.  (It's just "optimized".)
    return True


def _reset_problem_attempts_for_student(request, course_id, problem_url, student_identifier):
    action_name = 'reset'
    update_fcn = _reset_problem_attempts_module_state
    return _update_problem_module_state_for_student(request, course_id, problem_url, student_identifier,
                                                    update_fcn, action_name)


def _reset_problem_attempts_for_all_students(request, course_id, problem_url):
    action_name = 'reset'
    update_fcn = _reset_problem_attempts_module_state
    return _update_problem_module_state_for_all_students(request, course_id, problem_url,
                                                         update_fcn, action_name)


def _delete_problem_module_state(request, module_to_delete, module_descriptor):
    '''
    delete the state
    '''
    module_to_delete.delete()
    return True


def _delete_problem_state_for_student(request, course_id, problem_url, student_ident):
    action_name = 'deleted'
    update_fcn = _delete_problem_module_state
    return _update_problem_module_state_for_student(request, course_id, problem_url,
                                                    update_fcn, action_name)


def _delete_problem_state_for_all_students(request, course_id, problem_url):
    action_name = 'deleted'
    update_fcn = _delete_problem_module_state
    return _update_problem_module_state_for_all_students(request, course_id, problem_url,
                                                         update_fcn, action_name)
