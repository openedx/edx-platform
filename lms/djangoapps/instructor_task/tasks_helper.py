"""
This file contains tasks that are designed to perform background operations on the
running state of a course.

"""
import json
import urllib
from datetime import datetime
from time import time

from celery import Task, current_task
from celery.utils.log import get_task_logger
from celery.states import SUCCESS, FAILURE
from django.contrib.auth.models import User
from django.db import transaction, reset_queries
from dogapi import dog_stats_api
from pytz import UTC

from xmodule.modulestore.django import modulestore
from track.views import task_track

from courseware.grades import iterate_grades_for
from courseware.models import StudentModule
from courseware.model_data import FieldDataCache
from courseware.module_render import get_module_for_descriptor_internal
from instructor_task.models import ReportStore, InstructorTask, PROGRESS
from student.models import CourseEnrollment

# define different loggers for use within tasks and on client side
TASK_LOG = get_task_logger(__name__)

# define value to use when no task_id is provided:
UNKNOWN_TASK_ID = 'unknown-task_id'

# define values for update functions to use to return status to perform_module_state_update
UPDATE_STATUS_SUCCEEDED = 'succeeded'
UPDATE_STATUS_FAILED = 'failed'
UPDATE_STATUS_SKIPPED = 'skipped'


class BaseInstructorTask(Task):
    """
    Base task class for use with InstructorTask models.

    Permits updating information about task in corresponding InstructorTask for monitoring purposes.

    Assumes that the entry_id of the InstructorTask model is the first argument to the task.

    The `entry_id` is the primary key for the InstructorTask entry representing the task.  This class
    updates the entry on success and failure of the task it wraps.  It is setting the entry's value
    for task_state based on what Celery would set it to once the task returns to Celery:
    FAILURE if an exception is encountered, and SUCCESS if it returns normally.
    Other arguments are pass-throughs to perform_module_state_update, and documented there.
    """
    abstract = True

    def on_success(self, task_progress, task_id, args, kwargs):
        """
        Update InstructorTask object corresponding to this task with info about success.

        Updates task_output and task_state.  But it shouldn't actually do anything
        if the task is only creating subtasks to actually do the work.

        Assumes `task_progress` is a dict containing the task's result, with the following keys:

          'attempted': number of attempts made
          'succeeded': number of attempts that "succeeded"
          'skipped': number of attempts that "skipped"
          'failed': number of attempts that "failed"
          'total': number of possible subtasks to attempt
          'action_name': user-visible verb to use in status messages.  Should be past-tense.
              Pass-through of input `action_name`.
          'duration_ms': how long the task has (or had) been running.

        This is JSON-serialized and stored in the task_output column of the InstructorTask entry.

        """
        TASK_LOG.debug('Task %s: success returned with progress: %s', task_id, task_progress)
        # We should be able to find the InstructorTask object to update
        # based on the task_id here, without having to dig into the
        # original args to the task.  On the other hand, the entry_id
        # is the first value passed to all such args, so we'll use that.
        # And we assume that it exists, else we would already have had a failure.
        entry_id = args[0]
        entry = InstructorTask.objects.get(pk=entry_id)
        # Check to see if any subtasks had been defined as part of this task.
        # If not, then we know that we're done.  (If so, let the subtasks
        # handle updating task_state themselves.)
        if len(entry.subtasks) == 0:
            entry.task_output = InstructorTask.create_output_for_success(task_progress)
            entry.task_state = SUCCESS
            entry.save_now()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Update InstructorTask object corresponding to this task with info about failure.

        Fetches and updates exception and traceback information on failure.

        If an exception is raised internal to the task, it is caught by celery and provided here.
        The information is recorded in the InstructorTask object as a JSON-serialized dict
        stored in the task_output column.  It contains the following keys:

               'exception':  type of exception object
               'message': error message from exception object
               'traceback': traceback information (truncated if necessary)

        Note that there is no way to record progress made within the task (e.g. attempted,
        succeeded, etc.) when such failures occur.
        """
        TASK_LOG.debug(u'Task %s: failure returned', task_id)
        entry_id = args[0]
        try:
            entry = InstructorTask.objects.get(pk=entry_id)
        except InstructorTask.DoesNotExist:
            # if the InstructorTask object does not exist, then there's no point
            # trying to update it.
            TASK_LOG.error(u"Task (%s) has no InstructorTask object for id %s", task_id, entry_id)
        else:
            TASK_LOG.warning(u"Task (%s) failed", task_id, exc_info=True)
            entry.task_output = InstructorTask.create_output_for_failure(einfo.exception, einfo.traceback)
            entry.task_state = FAILURE
            entry.save_now()


class UpdateProblemModuleStateError(Exception):
    """
    Error signaling a fatal condition while updating problem modules.

    Used when the current module cannot be processed and no more
    modules should be attempted.
    """
    pass


def _get_current_task():
    """
    Stub to make it easier to test without actually running Celery.

    This is a wrapper around celery.current_task, which provides access
    to the top of the stack of Celery's tasks.  When running tests, however,
    it doesn't seem to work to mock current_task directly, so this wrapper
    is used to provide a hook to mock in tests, while providing the real
    `current_task` in production.
    """
    return current_task


def run_main_task(entry_id, task_fcn, action_name):
    """
    Applies the `task_fcn` to the arguments defined in `entry_id` InstructorTask.

    Arguments passed to `task_fcn` are:

     `entry_id` : the primary key for the InstructorTask entry representing the task.
     `course_id` : the id for the course.
     `task_input` : dict containing task-specific arguments, JSON-decoded from InstructorTask's task_input.
     `action_name` : past-tense verb to use for constructing status messages.

    If no exceptions are raised, the `task_fcn` should return a dict containing
    the task's result with the following keys:

          'attempted': number of attempts made
          'succeeded': number of attempts that "succeeded"
          'skipped': number of attempts that "skipped"
          'failed': number of attempts that "failed"
          'total': number of possible subtasks to attempt
          'action_name': user-visible verb to use in status messages.
              Should be past-tense.  Pass-through of input `action_name`.
          'duration_ms': how long the task has (or had) been running.

    """

    # get the InstructorTask to be updated.  If this fails, then let the exception return to Celery.
    # There's no point in catching it here.
    entry = InstructorTask.objects.get(pk=entry_id)

    # get inputs to use in this task from the entry:
    task_id = entry.task_id
    course_id = entry.course_id
    task_input = json.loads(entry.task_input)

    # construct log message:
    fmt = u'task "{task_id}": course "{course_id}" input "{task_input}"'
    task_info_string = fmt.format(task_id=task_id, course_id=course_id, task_input=task_input)

    TASK_LOG.info('Starting update (nothing %s yet): %s', action_name, task_info_string)

    # Check that the task_id submitted in the InstructorTask matches the current task
    # that is running.
    request_task_id = _get_current_task().request.id
    if task_id != request_task_id:
        fmt = u'Requested task did not match actual task "{actual_id}": {task_info}'
        message = fmt.format(actual_id=request_task_id, task_info=task_info_string)
        TASK_LOG.error(message)
        raise ValueError(message)

    # Now do the work:
    with dog_stats_api.timer('instructor_tasks.time.overall', tags=['action:{name}'.format(name=action_name)]):
        task_progress = task_fcn(entry_id, course_id, task_input, action_name)

    # Release any queries that the connection has been hanging onto:
    reset_queries()

    # log and exit, returning task_progress info as task result:
    TASK_LOG.info('Finishing %s: final: %s', task_info_string, task_progress)
    return task_progress


def perform_module_state_update(update_fcn, filter_fcn, _entry_id, course_id, task_input, action_name):
    """
    Performs generic update by visiting StudentModule instances with the update_fcn provided.

    StudentModule instances are those that match the specified `course_id` and `module_state_key`.
    If `student_identifier` is not None, it is used as an additional filter to limit the modules to those belonging
    to that student. If `student_identifier` is None, performs update on modules for all students on the specified problem.

    If a `filter_fcn` is not None, it is applied to the query that has been constructed.  It takes one
    argument, which is the query being filtered, and returns the filtered version of the query.

    The `update_fcn` is called on each StudentModule that passes the resulting filtering.
    It is passed three arguments:  the module_descriptor for the module pointed to by the
    module_state_key, the particular StudentModule to update, and the xmodule_instance_args being
    passed through.  If the value returned by the update function evaluates to a boolean True,
    the update is successful; False indicates the update on the particular student module failed.
    A raised exception indicates a fatal condition -- that no other student modules should be considered.

    The return value is a dict containing the task's results, with the following keys:

          'attempted': number of attempts made
          'succeeded': number of attempts that "succeeded"
          'skipped': number of attempts that "skipped"
          'failed': number of attempts that "failed"
          'total': number of possible updates to attempt
          'action_name': user-visible verb to use in status messages.  Should be past-tense.
              Pass-through of input `action_name`.
          'duration_ms': how long the task has (or had) been running.

    Because this is run internal to a task, it does not catch exceptions.  These are allowed to pass up to the
    next level, so that it can set the failure modes and capture the error trace in the InstructorTask and the
    result object.

    """
    # get start time for task:
    start_time = time()

    usage_key = course_id.make_usage_key_from_deprecated_string(task_input.get('problem_url'))
    student_identifier = task_input.get('student')

    # find the problem descriptor:
    module_descriptor = modulestore().get_item(usage_key)

    # find the module in question
    modules_to_update = StudentModule.objects.filter(course_id=course_id, module_state_key=usage_key)

    # give the option of updating an individual student. If not specified,
    # then updates all students who have responded to a problem so far
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
    num_attempted = 0
    num_succeeded = 0
    num_skipped = 0
    num_failed = 0
    num_total = modules_to_update.count()

    def get_task_progress():
        """Return a dict containing info about current task"""
        current_time = time()
        progress = {'action_name': action_name,
                    'attempted': num_attempted,
                    'succeeded': num_succeeded,
                    'skipped': num_skipped,
                    'failed': num_failed,
                    'total': num_total,
                    'duration_ms': int((current_time - start_time) * 1000),
                    }
        return progress

    task_progress = get_task_progress()
    _get_current_task().update_state(state=PROGRESS, meta=task_progress)
    for module_to_update in modules_to_update:
        num_attempted += 1
        # There is no try here:  if there's an error, we let it throw, and the task will
        # be marked as FAILED, with a stack trace.
        with dog_stats_api.timer('instructor_tasks.module.time.step', tags=[u'action:{name}'.format(name=action_name)]):
            update_status = update_fcn(module_descriptor, module_to_update)
            if update_status == UPDATE_STATUS_SUCCEEDED:
                # If the update_fcn returns true, then it performed some kind of work.
                # Logging of failures is left to the update_fcn itself.
                num_succeeded += 1
            elif update_status == UPDATE_STATUS_FAILED:
                num_failed += 1
            elif update_status == UPDATE_STATUS_SKIPPED:
                num_skipped += 1
            else:
                raise UpdateProblemModuleStateError("Unexpected update_status returned: {}".format(update_status))

        # update task status:
        task_progress = get_task_progress()
        _get_current_task().update_state(state=PROGRESS, meta=task_progress)

    return task_progress


def _get_task_id_from_xmodule_args(xmodule_instance_args):
    """Gets task_id from `xmodule_instance_args` dict, or returns default value if missing."""
    return xmodule_instance_args.get('task_id', UNKNOWN_TASK_ID) if xmodule_instance_args is not None else UNKNOWN_TASK_ID


def _get_xqueue_callback_url_prefix(xmodule_instance_args):
    """Gets prefix to use when constructing xqueue_callback_url."""
    return xmodule_instance_args.get('xqueue_callback_url_prefix', '') if xmodule_instance_args is not None else ''


def _get_track_function_for_task(student, xmodule_instance_args=None, source_page='x_module_task'):
    """
    Make a tracking function that logs what happened.

    For insertion into ModuleSystem, and used by CapaModule, which will
    provide the event_type (as string) and event (as dict) as arguments.
    The request_info and task_info (and page) are provided here.
    """
    # get request-related tracking information from args passthrough, and supplement with task-specific
    # information:
    request_info = xmodule_instance_args.get('request_info', {}) if xmodule_instance_args is not None else {}
    task_info = {'student': student.username, 'task_id': _get_task_id_from_xmodule_args(xmodule_instance_args)}

    return lambda event_type, event: task_track(request_info, task_info, event_type, event, page=source_page)


def _get_module_instance_for_task(course_id, student, module_descriptor, xmodule_instance_args=None,
                                  grade_bucket_type=None):
    """
    Fetches a StudentModule instance for a given `course_id`, `student` object, and `module_descriptor`.

    `xmodule_instance_args` is used to provide information for creating a track function and an XQueue callback.
    These are passed, along with `grade_bucket_type`, to get_module_for_descriptor_internal, which sidesteps
    the need for a Request object when instantiating an xmodule instance.
    """
    # reconstitute the problem's corresponding XModule:
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(course_id, student, module_descriptor)

    # get request-related tracking information from args passthrough, and supplement with task-specific
    # information:
    request_info = xmodule_instance_args.get('request_info', {}) if xmodule_instance_args is not None else {}
    task_info = {"student": student.username, "task_id": _get_task_id_from_xmodule_args(xmodule_instance_args)}

    def make_track_function():
        '''
        Make a tracking function that logs what happened.

        For insertion into ModuleSystem, and used by CapaModule, which will
        provide the event_type (as string) and event (as dict) as arguments.
        The request_info and task_info (and page) are provided here.
        '''
        return lambda event_type, event: task_track(request_info, task_info, event_type, event, page='x_module_task')

    xqueue_callback_url_prefix = xmodule_instance_args.get('xqueue_callback_url_prefix', '') \
        if xmodule_instance_args is not None else ''

    return get_module_for_descriptor_internal(
        user=student,
        descriptor=module_descriptor,
        field_data_cache=field_data_cache,
        course_id=course_id,
        track_function=make_track_function(),
        xqueue_callback_url_prefix=xqueue_callback_url_prefix,
        grade_bucket_type=grade_bucket_type,
        # This module isn't being used for front-end rendering
        request_token=None,
    )


@transaction.autocommit
def rescore_problem_module_state(xmodule_instance_args, module_descriptor, student_module):
    '''
    Takes an XModule descriptor and a corresponding StudentModule object, and
    performs rescoring on the student's problem submission.

    Throws exceptions if the rescoring is fatal and should be aborted if in a loop.
    In particular, raises UpdateProblemModuleStateError if module fails to instantiate,
    or if the module doesn't support rescoring.

    Returns True if problem was successfully rescored for the given student, and False
    if problem encountered some kind of error in rescoring.
    '''
    # unpack the StudentModule:
    course_id = student_module.course_id
    student = student_module.student
    usage_key = student_module.module_state_key
    instance = _get_module_instance_for_task(course_id, student, module_descriptor, xmodule_instance_args, grade_bucket_type='rescore')

    if instance is None:
        # Either permissions just changed, or someone is trying to be clever
        # and load something they shouldn't have access to.
        msg = "No module {loc} for student {student}--access denied?".format(loc=usage_key,
                                                                             student=student)
        TASK_LOG.debug(msg)
        raise UpdateProblemModuleStateError(msg)

    if not hasattr(instance, 'rescore_problem'):
        # This should also not happen, since it should be already checked in the caller,
        # but check here to be sure.
        msg = "Specified problem does not support rescoring."
        raise UpdateProblemModuleStateError(msg)

    result = instance.rescore_problem()
    instance.save()
    if 'success' not in result:
        # don't consider these fatal, but false means that the individual call didn't complete:
        TASK_LOG.warning(u"error processing rescore call for course {course}, problem {loc} and student {student}: "
                         u"unexpected response {msg}".format(msg=result, course=course_id, loc=usage_key, student=student))
        return UPDATE_STATUS_FAILED
    elif result['success'] not in ['correct', 'incorrect']:
        TASK_LOG.warning(u"error processing rescore call for course {course}, problem {loc} and student {student}: "
                         u"{msg}".format(msg=result['success'], course=course_id, loc=usage_key, student=student))
        return UPDATE_STATUS_FAILED
    else:
        TASK_LOG.debug(u"successfully processed rescore call for course {course}, problem {loc} and student {student}: "
                       u"{msg}".format(msg=result['success'], course=course_id, loc=usage_key, student=student))
        return UPDATE_STATUS_SUCCEEDED


@transaction.autocommit
def reset_attempts_module_state(xmodule_instance_args, _module_descriptor, student_module):
    """
    Resets problem attempts to zero for specified `student_module`.

    Returns a status of UPDATE_STATUS_SUCCEEDED if a problem has non-zero attempts
    that are being reset, and UPDATE_STATUS_SKIPPED otherwise.
    """
    update_status = UPDATE_STATUS_SKIPPED
    problem_state = json.loads(student_module.state) if student_module.state else {}
    if 'attempts' in problem_state:
        old_number_of_attempts = problem_state["attempts"]
        if old_number_of_attempts > 0:
            problem_state["attempts"] = 0
            # convert back to json and save
            student_module.state = json.dumps(problem_state)
            student_module.save()
            # get request-related tracking information from args passthrough,
            # and supplement with task-specific information:
            track_function = _get_track_function_for_task(student_module.student, xmodule_instance_args)
            event_info = {"old_attempts": old_number_of_attempts, "new_attempts": 0}
            track_function('problem_reset_attempts', event_info)
            update_status = UPDATE_STATUS_SUCCEEDED

    return update_status


@transaction.autocommit
def delete_problem_module_state(xmodule_instance_args, _module_descriptor, student_module):
    """
    Delete the StudentModule entry.

    Always returns UPDATE_STATUS_SUCCEEDED, indicating success, if it doesn't raise an exception due to database error.
    """
    student_module.delete()
    # get request-related tracking information from args passthrough,
    # and supplement with task-specific information:
    track_function = _get_track_function_for_task(student_module.student, xmodule_instance_args)
    track_function('problem_delete_state', {})
    return UPDATE_STATUS_SUCCEEDED


def push_grades_to_s3(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a grades CSV file for all students that
    are enrolled, and store using a `ReportStore`. Once created, the files can
    be accessed by instantiating another `ReportStore` (via
    `ReportStore.from_config()`) and calling `link_for()` on it. Writes are
    buffered, so we'll never write part of a CSV file to S3 -- i.e. any files
    that are visible in ReportStore will be complete ones.

    As we start to add more CSV downloads, it will probably be worthwhile to
    make a more general CSVDoc class instead of building out the rows like we
    do here.
    """
    start_time = datetime.now(UTC)
    status_interval = 100

    enrolled_students = CourseEnrollment.users_enrolled_in(course_id)
    num_total = enrolled_students.count()
    num_attempted = 0
    num_succeeded = 0
    num_failed = 0
    curr_step = "Calculating Grades"

    def update_task_progress():
        """Return a dict containing info about current task"""
        current_time = datetime.now(UTC)
        progress = {
            'action_name': action_name,
            'attempted': num_attempted,
            'succeeded': num_succeeded,
            'failed': num_failed,
            'total': num_total,
            'duration_ms': int((current_time - start_time).total_seconds() * 1000),
            'step': curr_step,
        }
        _get_current_task().update_state(state=PROGRESS, meta=progress)

        return progress

    # Loop over all our students and build our CSV lists in memory
    header = None
    rows = []
    err_rows = [["id", "username", "error_msg"]]
    for student, gradeset, err_msg in iterate_grades_for(course_id, enrolled_students):
        # Periodically update task status (this is a cache write)
        if num_attempted % status_interval == 0:
            update_task_progress()
        num_attempted += 1

        if gradeset:
            # We were able to successfully grade this student for this course.
            num_succeeded += 1
            if not header:
                # Encode the header row in utf-8 encoding in case there are unicode characters
                header = [section['label'].encode('utf-8') for section in gradeset[u'section_breakdown']]
                rows.append(["id", "email", "username", "grade"] + header)

            percents = {
                section['label']: section.get('percent', 0.0)
                for section in gradeset[u'section_breakdown']
                if 'label' in section
            }

            # Not everybody has the same gradable items. If the item is not
            # found in the user's gradeset, just assume it's a 0. The aggregated
            # grades for their sections and overall course will be calculated
            # without regard for the item they didn't have access to, so it's
            # possible for a student to have a 0.0 show up in their row but
            # still have 100% for the course.
            row_percents = [percents.get(label, 0.0) for label in header]
            rows.append([student.id, student.email.encode('utf-8'), student.username, gradeset['percent']] + row_percents)
        else:
            # An empty gradeset means we failed to grade a student.
            num_failed += 1
            err_rows.append([student.id, student.username, err_msg])

    # By this point, we've got the rows we're going to stuff into our CSV files.
    curr_step = "Uploading CSVs"
    update_task_progress()

    # Generate parts of the file name
    timestamp_str = start_time.strftime("%Y-%m-%d-%H%M")
    course_id_prefix = urllib.quote(course_id.to_deprecated_string().replace("/", "_"))

    # Perform the actual upload
    report_store = ReportStore.from_config()
    report_store.store_rows(
        course_id,
        u"{}_grade_report_{}.csv".format(course_id_prefix, timestamp_str),
        rows
    )

    # If there are any error rows (don't count the header), write them out as well
    if len(err_rows) > 1:
        report_store.store_rows(
            course_id,
            u"{}_grade_report_{}_err.csv".format(course_id_prefix, timestamp_str),
            err_rows
        )

    # One last update before we close out...
    return update_task_progress()
