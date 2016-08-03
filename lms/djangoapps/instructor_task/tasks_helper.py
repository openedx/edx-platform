"""
This file contains tasks that are designed to perform background operations on the
running state of a course.

"""
import json
import re
from collections import OrderedDict
from datetime import datetime
from django.conf import settings
from eventtracking import tracker
from itertools import chain
from time import time
import unicodecsv
import logging

from celery import Task, current_task
from celery.states import SUCCESS, FAILURE
from django.contrib.auth.models import User
from django.core.files.storage import DefaultStorage
from django.db import reset_queries
from django.db.models import Q
import dogstats_wrapper as dog_stats_api
from pytz import UTC
from StringIO import StringIO
from edxmako.shortcuts import render_to_string
from instructor.paidcourse_enrollment_report import PaidCourseEnrollmentReportProvider
from shoppingcart.models import (
    PaidCourseRegistration, CourseRegCodeItem, InvoiceTransaction,
    Invoice, CouponRedemption, RegistrationCodeRedemption, CourseRegistrationCode
)
from survey.models import SurveyAnswer

from track.views import task_track
from util.db import outer_atomic
from util.file import course_filename_prefix_generator, UniversalNewlineIterator
from xblock.runtime import KvsFieldData
from xmodule.modulestore.django import modulestore
from xmodule.split_test_module import get_split_user_partitions
from django.utils.translation import ugettext as _
from certificates.models import (
    CertificateWhitelist,
    certificate_info_for_user,
    CertificateStatuses,
    GeneratedCertificate
)
from certificates.api import generate_user_certificates
from courseware.courses import get_course_by_id, get_problems_in_section
from lms.djangoapps.grades.course_grades import iterate_grades_for
from courseware.models import StudentModule
from courseware.model_data import DjangoKeyValueStore, FieldDataCache
from courseware.module_render import get_module_for_descriptor_internal
from instructor_analytics.basic import (
    enrolled_students_features,
    get_proctored_exam_results,
    list_may_enroll,
    list_problem_responses
)
from instructor_analytics.csvs import format_dictlist
from openassessment.data import OraAggregateData
from instructor_task.models import ReportStore, InstructorTask, PROGRESS
from lms.djangoapps.lms_xblock.runtime import LmsPartitionService
from openedx.core.djangoapps.course_groups.cohorts import get_cohort
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
from openedx.core.djangoapps.content.course_structures.models import CourseStructure
from opaque_keys.edx.keys import UsageKey
from openedx.core.djangoapps.course_groups.cohorts import add_user_to_cohort, is_course_cohorted
from student.models import CourseEnrollment, CourseAccessRole
from lms.djangoapps.teams.models import CourseTeamMembership
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification

# define different loggers for use within tasks and on client side
TASK_LOG = logging.getLogger('edx.celery.task')

# define value to use when no task_id is provided:
UNKNOWN_TASK_ID = 'unknown-task_id'
FILTERED_OUT_ROLES = ['staff', 'instructor', 'finance_admin', 'sales_admin']
# define values for update functions to use to return status to perform_module_state_update
UPDATE_STATUS_SUCCEEDED = 'succeeded'
UPDATE_STATUS_FAILED = 'failed'
UPDATE_STATUS_SKIPPED = 'skipped'

# The setting name used for events when "settings" (account settings, preferences, profile information) change.
REPORT_REQUESTED_EVENT_NAME = u'edx.instructor.report.requested'


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


class TaskProgress(object):
    """
    Encapsulates the current task's progress by keeping track of
    'attempted', 'succeeded', 'skipped', 'failed', 'total',
    'action_name', and 'duration_ms' values.
    """
    def __init__(self, action_name, total, start_time):
        self.action_name = action_name
        self.total = total
        self.start_time = start_time
        self.attempted = 0
        self.succeeded = 0
        self.skipped = 0
        self.failed = 0

    def update_task_state(self, extra_meta=None):
        """
        Update the current celery task's state to the progress state
        specified by the current object.  Returns the progress
        dictionary for use by `run_main_task` and
        `BaseInstructorTask.on_success`.

        Arguments:
            extra_meta (dict): Extra metadata to pass to `update_state`

        Returns:
            dict: The current task's progress dict
        """
        progress_dict = {
            'action_name': self.action_name,
            'attempted': self.attempted,
            'succeeded': self.succeeded,
            'skipped': self.skipped,
            'failed': self.failed,
            'total': self.total,
            'duration_ms': int((time() - self.start_time) * 1000),
        }
        if extra_meta is not None:
            progress_dict.update(extra_meta)
        _get_current_task().update_state(state=PROGRESS, meta=progress_dict)
        return progress_dict


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

    # Get the InstructorTask to be updated. If this fails then let the exception return to Celery.
    # There's no point in catching it here.
    with outer_atomic():
        entry = InstructorTask.objects.get(pk=entry_id)
        entry.task_state = PROGRESS
        entry.save_now()

    # Get inputs to use in this task from the entry
    task_id = entry.task_id
    course_id = entry.course_id
    task_input = json.loads(entry.task_input)

    # Construct log message
    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(task_id=task_id, entry_id=entry_id, course_id=course_id, task_input=task_input)
    TASK_LOG.info(u'%s, Starting update (nothing %s yet)', task_info_string, action_name)

    # Check that the task_id submitted in the InstructorTask matches the current task
    # that is running.
    request_task_id = _get_current_task().request.id
    if task_id != request_task_id:
        fmt = u'{task_info}, Requested task did not match actual task "{actual_id}"'
        message = fmt.format(task_info=task_info_string, actual_id=request_task_id)
        TASK_LOG.error(message)
        raise ValueError(message)

    # Now do the work
    with dog_stats_api.timer('instructor_tasks.time.overall', tags=[u'action:{name}'.format(name=action_name)]):
        task_progress = task_fcn(entry_id, course_id, task_input, action_name)

    # Release any queries that the connection has been hanging onto
    reset_queries()

    # Log and exit, returning task_progress info as task result
    TASK_LOG.info(u'%s, Task type: %s, Finishing task: %s', task_info_string, action_name, task_progress)
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
    start_time = time()
    usage_keys = []
    problem_url = task_input.get('problem_url')
    entrance_exam_url = task_input.get('entrance_exam_url')
    student_identifier = task_input.get('student')
    problems = {}

    # if problem_url is present make a usage key from it
    if problem_url:
        usage_key = course_id.make_usage_key_from_deprecated_string(problem_url)
        usage_keys.append(usage_key)

        # find the problem descriptor:
        problem_descriptor = modulestore().get_item(usage_key)
        problems[unicode(usage_key)] = problem_descriptor

    # if entrance_exam is present grab all problems in it
    if entrance_exam_url:
        problems = get_problems_in_section(entrance_exam_url)
        usage_keys = [UsageKey.from_string(location) for location in problems.keys()]

    # find the modules in question
    modules_to_update = StudentModule.objects.filter(course_id=course_id, module_state_key__in=usage_keys)

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

    task_progress = TaskProgress(action_name, modules_to_update.count(), start_time)
    task_progress.update_task_state()

    for module_to_update in modules_to_update:
        task_progress.attempted += 1
        module_descriptor = problems[unicode(module_to_update.module_state_key)]
        # There is no try here:  if there's an error, we let it throw, and the task will
        # be marked as FAILED, with a stack trace.
        with dog_stats_api.timer('instructor_tasks.module.time.step', tags=[u'action:{name}'.format(name=action_name)]):
            update_status = update_fcn(module_descriptor, module_to_update)
            if update_status == UPDATE_STATUS_SUCCEEDED:
                # If the update_fcn returns true, then it performed some kind of work.
                # Logging of failures is left to the update_fcn itself.
                task_progress.succeeded += 1
            elif update_status == UPDATE_STATUS_FAILED:
                task_progress.failed += 1
            elif update_status == UPDATE_STATUS_SKIPPED:
                task_progress.skipped += 1
            else:
                raise UpdateProblemModuleStateError("Unexpected update_status returned: {}".format(update_status))

    return task_progress.update_task_state()


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
                                  grade_bucket_type=None, course=None):
    """
    Fetches a StudentModule instance for a given `course_id`, `student` object, and `module_descriptor`.

    `xmodule_instance_args` is used to provide information for creating a track function and an XQueue callback.
    These are passed, along with `grade_bucket_type`, to get_module_for_descriptor_internal, which sidesteps
    the need for a Request object when instantiating an xmodule instance.
    """
    # reconstitute the problem's corresponding XModule:
    field_data_cache = FieldDataCache.cache_for_descriptor_descendents(course_id, student, module_descriptor)
    student_data = KvsFieldData(DjangoKeyValueStore(field_data_cache))

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
        student_data=student_data,
        course_id=course_id,
        track_function=make_track_function(),
        xqueue_callback_url_prefix=xqueue_callback_url_prefix,
        grade_bucket_type=grade_bucket_type,
        # This module isn't being used for front-end rendering
        request_token=None,
        # pass in a loaded course for override enabling
        course=course
    )


@outer_atomic
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

    with modulestore().bulk_operations(course_id):
        course = get_course_by_id(course_id)
        # TODO: Here is a call site where we could pass in a loaded course.  I
        # think we certainly need it since grading is happening here, and field
        # overrides would be important in handling that correctly
        instance = _get_module_instance_for_task(
            course_id,
            student,
            module_descriptor,
            xmodule_instance_args,
            grade_bucket_type='rescore',
            course=course
        )

        if instance is None:
            # Either permissions just changed, or someone is trying to be clever
            # and load something they shouldn't have access to.
            msg = "No module {loc} for student {student}--access denied?".format(
                loc=usage_key,
                student=student
            )
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
            TASK_LOG.warning(
                u"error processing rescore call for course %(course)s, problem %(loc)s "
                u"and student %(student)s: unexpected response %(msg)s",
                dict(
                    msg=result,
                    course=course_id,
                    loc=usage_key,
                    student=student
                )
            )
            return UPDATE_STATUS_FAILED
        elif result['success'] not in ['correct', 'incorrect']:
            TASK_LOG.warning(
                u"error processing rescore call for course %(course)s, problem %(loc)s "
                u"and student %(student)s: %(msg)s",
                dict(
                    msg=result['success'],
                    course=course_id,
                    loc=usage_key,
                    student=student
                )
            )
            return UPDATE_STATUS_FAILED
        else:
            TASK_LOG.debug(
                u"successfully processed rescore call for course %(course)s, problem %(loc)s "
                u"and student %(student)s: %(msg)s",
                dict(
                    msg=result['success'],
                    course=course_id,
                    loc=usage_key,
                    student=student
                )
            )
            return UPDATE_STATUS_SUCCEEDED


@outer_atomic
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


@outer_atomic
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


def upload_csv_to_report_store(rows, csv_name, course_id, timestamp, config_name='GRADES_DOWNLOAD'):
    """
    Upload data as a CSV using ReportStore.

    Arguments:
        rows: CSV data in the following format (first column may be a
            header):
            [
                [row1_colum1, row1_colum2, ...],
                ...
            ]
        csv_name: Name of the resulting CSV
        course_id: ID of the course
    """
    report_store = ReportStore.from_config(config_name)
    report_store.store_rows(
        course_id,
        u"{course_prefix}_{csv_name}_{timestamp_str}.csv".format(
            course_prefix=course_filename_prefix_generator(course_id),
            csv_name=csv_name,
            timestamp_str=timestamp.strftime("%Y-%m-%d-%H%M")
        ),
        rows
    )
    tracker.emit(REPORT_REQUESTED_EVENT_NAME, {"report_type": csv_name, })


def upload_exec_summary_to_store(data_dict, report_name, course_id, generated_at, config_name='FINANCIAL_REPORTS'):
    """
    Upload Executive Summary Html file using ReportStore.

    Arguments:
        data_dict: containing executive report data.
        report_name: Name of the resulting Html File.
        course_id: ID of the course
    """
    report_store = ReportStore.from_config(config_name)

    # Use the data dict and html template to generate the output buffer
    output_buffer = StringIO(render_to_string("instructor/instructor_dashboard_2/executive_summary.html", data_dict))

    report_store.store(
        course_id,
        u"{course_prefix}_{report_name}_{timestamp_str}.html".format(
            course_prefix=course_filename_prefix_generator(course_id),
            report_name=report_name,
            timestamp_str=generated_at.strftime("%Y-%m-%d-%H%M")
        ),
        output_buffer,
    )
    tracker.emit(REPORT_REQUESTED_EVENT_NAME, {"report_type": report_name})


def upload_grades_csv(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):  # pylint: disable=too-many-statements
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
    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    course = get_course_by_id(course_id)
    course_is_cohorted = is_course_cohorted(course.id)
    teams_enabled = course.teams_enabled
    cohorts_header = ['Cohort Name'] if course_is_cohorted else []
    teams_header = ['Team Name'] if teams_enabled else []

    experiment_partitions = get_split_user_partitions(course.user_partitions)
    group_configs_header = [u'Experiment Group ({})'.format(partition.name) for partition in experiment_partitions]

    certificate_info_header = ['Certificate Eligible', 'Certificate Delivered', 'Certificate Type']
    certificate_whitelist = CertificateWhitelist.objects.filter(course_id=course_id, whitelist=True)
    whitelisted_user_ids = [entry.user_id for entry in certificate_whitelist]

    # Loop over all our students and build our CSV lists in memory
    header = None
    rows = []
    err_rows = [["id", "username", "error_msg"]]
    current_step = {'step': 'Calculating Grades'}

    total_enrolled_students = enrolled_students.count()
    student_counter = 0
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, Starting grade calculation for total students: %s',
        task_info_string,
        action_name,
        current_step,

        total_enrolled_students
    )
    for student, gradeset, err_msg in iterate_grades_for(course_id, enrolled_students):
        # Periodically update task status (this is a cache write)
        if task_progress.attempted % status_interval == 0:
            task_progress.update_task_state(extra_meta=current_step)
        task_progress.attempted += 1

        # Now add a log entry after each student is graded to get a sense
        # of the task's progress
        student_counter += 1
        TASK_LOG.info(
            u'%s, Task type: %s, Current step: %s, Grade calculation in-progress for students: %s/%s',
            task_info_string,
            action_name,
            current_step,
            student_counter,
            total_enrolled_students
        )

        if gradeset:
            # We were able to successfully grade this student for this course.
            task_progress.succeeded += 1
            if not header:
                header = [section['label'] for section in gradeset[u'section_breakdown']]
                rows.append(
                    ["id", "email", "username", "grade"] + header + cohorts_header +
                    group_configs_header + teams_header +
                    ['Enrollment Track', 'Verification Status'] + certificate_info_header
                )

            percents = {
                section['label']: section.get('percent', 0.0)
                for section in gradeset[u'section_breakdown']
                if 'label' in section
            }

            cohorts_group_name = []
            if course_is_cohorted:
                group = get_cohort(student, course_id, assign=False)
                cohorts_group_name.append(group.name if group else '')

            group_configs_group_names = []
            for partition in experiment_partitions:
                group = LmsPartitionService(student, course_id).get_group(partition, assign=False)
                group_configs_group_names.append(group.name if group else '')

            team_name = []
            if teams_enabled:
                try:
                    membership = CourseTeamMembership.objects.get(user=student, team__course_id=course_id)
                    team_name.append(membership.team.name)
                except CourseTeamMembership.DoesNotExist:
                    team_name.append('')

            enrollment_mode = CourseEnrollment.enrollment_mode_for_user(student, course_id)[0]
            verification_status = SoftwareSecurePhotoVerification.verification_status_for_user(
                student,
                course_id,
                enrollment_mode
            )
            certificate_info = certificate_info_for_user(
                student,
                course_id,
                gradeset['grade'],
                student.id in whitelisted_user_ids
            )

            # Not everybody has the same gradable items. If the item is not
            # found in the user's gradeset, just assume it's a 0. The aggregated
            # grades for their sections and overall course will be calculated
            # without regard for the item they didn't have access to, so it's
            # possible for a student to have a 0.0 show up in their row but
            # still have 100% for the course.
            row_percents = [percents.get(label, 0.0) for label in header]
            rows.append(
                [student.id, student.email, student.username, gradeset['percent']] +
                row_percents + cohorts_group_name + group_configs_group_names + team_name +
                [enrollment_mode] + [verification_status] + certificate_info
            )
        else:
            # An empty gradeset means we failed to grade a student.
            task_progress.failed += 1
            err_rows.append([student.id, student.username, err_msg])

    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, Grade calculation completed for students: %s/%s',
        task_info_string,
        action_name,
        current_step,
        student_counter,
        total_enrolled_students
    )

    # By this point, we've got the rows we're going to stuff into our CSV files.
    current_step = {'step': 'Uploading CSVs'}
    task_progress.update_task_state(extra_meta=current_step)
    TASK_LOG.info(u'%s, Task type: %s, Current step: %s', task_info_string, action_name, current_step)

    # Perform the actual upload
    upload_csv_to_report_store(rows, 'grade_report', course_id, start_date)

    # If there are any error rows (don't count the header), write them out as well
    if len(err_rows) > 1:
        upload_csv_to_report_store(err_rows, 'grade_report_err', course_id, start_date)

    # One last update before we close out...
    TASK_LOG.info(u'%s, Task type: %s, Finalizing grade task', task_info_string, action_name)
    return task_progress.update_task_state(extra_meta=current_step)


def _order_problems(blocks):
    """
    Sort the problems by the assignment type and assignment that it belongs to.

    Args:
        blocks (OrderedDict) - A course structure containing blocks that have been ordered
                              (i.e. when we iterate over them, we will see them in the order
                              that they appear in the course).

    Returns:
        an OrderedDict that maps a problem id to its headers in the final report.
    """
    problems = OrderedDict()
    assignments = OrderedDict()
    # First, sort out all the blocks into their correct assignments and all the
    # assignments into their correct types.
    for block in blocks:
        # Put the assignments in order into the assignments list.
        if blocks[block]['block_type'] == 'sequential':
            block_format = blocks[block]['format']
            if block_format not in assignments:
                assignments[block_format] = OrderedDict()
            assignments[block_format][block] = list()

        # Put the problems into the correct order within their assignment.
        if blocks[block]['block_type'] == 'problem' and blocks[block]['graded'] is True:
            current = blocks[block]['parent']
            # crawl up the tree for the sequential block
            while blocks[current]['block_type'] != 'sequential':
                current = blocks[current]['parent']

            current_format = blocks[current]['format']
            assignments[current_format][current].append(block)

    # Now that we have a sorting and an order for the assignments and problems,
    # iterate through them in order to generate the header row.
    for assignment_type in assignments:
        for assignment_index, assignment in enumerate(assignments[assignment_type].keys(), start=1):
            for problem in assignments[assignment_type][assignment]:
                header_name = u"{assignment_type} {assignment_index}: {assignment_name} - {block}".format(
                    block=blocks[problem]['display_name'],
                    assignment_type=assignment_type,
                    assignment_index=assignment_index,
                    assignment_name=blocks[assignment]['display_name']
                )
                problems[problem] = [header_name + " (Earned)", header_name + " (Possible)"]

    return problems


def upload_problem_responses_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    all student answers to a given problem, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating students answers to problem'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    problem_location = task_input.get('problem_location')
    student_data = list_problem_responses(course_id, problem_location)
    features = ['username', 'state']
    header, rows = format_dictlist(student_data, features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    problem_location = re.sub(r'[:/]', '_', problem_location)
    csv_name = 'student_state_from_{}'.format(problem_location)
    upload_csv_to_report_store(rows, csv_name, course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_problem_grade_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    Generate a CSV containing all students' problem grades within a given
    `course_id`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    # This struct encapsulates both the display names of each static item in the
    # header row as values as well as the django User field names of those items
    # as the keys.  It is structured in this way to keep the values related.
    header_row = OrderedDict([('id', 'Student ID'), ('email', 'Email'), ('username', 'Username')])

    try:
        course_structure = CourseStructure.objects.get(course_id=course_id)
        blocks = course_structure.ordered_blocks
        problems = _order_problems(blocks)
    except CourseStructure.DoesNotExist:
        return task_progress.update_task_state(
            extra_meta={'step': 'Generating course structure. Please refresh and try again.'}
        )

    # Just generate the static fields for now.
    rows = [list(header_row.values()) + ['Final Grade'] + list(chain.from_iterable(problems.values()))]
    error_rows = [list(header_row.values()) + ['error_msg']]
    current_step = {'step': 'Calculating Grades'}

    for student, gradeset, err_msg in iterate_grades_for(course_id, enrolled_students):
        student_fields = [getattr(student, field_name) for field_name in header_row]
        task_progress.attempted += 1

        if 'percent' not in gradeset or 'raw_scores' not in gradeset:
            # There was an error grading this student.
            # Generally there will be a non-empty err_msg, but that is not always the case.
            if not err_msg:
                err_msg = u"Unknown error"
            error_rows.append(student_fields + [err_msg])
            task_progress.failed += 1
            continue

        final_grade = gradeset['percent']
        # Only consider graded problems
        problem_scores = {unicode(score.module_id): score for score in gradeset['raw_scores'] if score.graded}
        earned_possible_values = list()
        for problem_id in problems:
            try:
                problem_score = problem_scores[problem_id]
                earned_possible_values.append([problem_score.earned, problem_score.possible])
            except KeyError:
                # The student has not been graded on this problem.  For example,
                # iterate_grades_for skips problems that students have never
                # seen in order to speed up report generation.  It could also be
                # the case that the student does not have access to it (e.g. A/B
                # test or cohorted courseware).
                earned_possible_values.append(['N/A', 'N/A'])
        rows.append(student_fields + [final_grade] + list(chain.from_iterable(earned_possible_values)))

        task_progress.succeeded += 1
        if task_progress.attempted % status_interval == 0:
            task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload if any students have been successfully graded
    if len(rows) > 1:
        upload_csv_to_report_store(rows, 'problem_grade_report', course_id, start_date)
    # If there are any error rows, write them out as well
    if len(error_rows) > 1:
        upload_csv_to_report_store(error_rows, 'problem_grade_report_err', course_id, start_date)

    return task_progress.update_task_state(extra_meta={'step': 'Uploading CSV'})


def upload_students_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing profile
    information for all students that are enrolled, and store using a
    `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    enrolled_students = CourseEnrollment.objects.users_enrolled_in(course_id)
    task_progress = TaskProgress(action_name, enrolled_students.count(), start_time)

    current_step = {'step': 'Calculating Profile Info'}
    task_progress.update_task_state(extra_meta=current_step)

    # compute the student features table and format it
    query_features = task_input
    student_data = enrolled_students_features(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'student_profile_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_enrollment_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing profile
    information for all students that are enrolled, and store using a
    `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    status_interval = 100
    students_in_course = CourseEnrollment.objects.enrolled_and_dropped_out_users(course_id)
    task_progress = TaskProgress(action_name, students_in_course.count(), start_time)

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    # Loop over all our students and build our CSV lists in memory
    rows = []
    header = None
    current_step = {'step': 'Gathering Profile Information'}
    enrollment_report_provider = PaidCourseEnrollmentReportProvider()
    total_students = students_in_course.count()
    student_counter = 0
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, generating detailed enrollment report for total students: %s',
        task_info_string,
        action_name,
        current_step,
        total_students
    )

    for student in students_in_course:
        # Periodically update task status (this is a cache write)
        if task_progress.attempted % status_interval == 0:
            task_progress.update_task_state(extra_meta=current_step)
        task_progress.attempted += 1

        # Now add a log entry after certain intervals to get a hint that task is in progress
        student_counter += 1
        if student_counter % 100 == 0:
            TASK_LOG.info(
                u'%s, Task type: %s, Current step: %s, gathering enrollment profile for students in progress: %s/%s',
                task_info_string,
                action_name,
                current_step,
                student_counter,
                total_students
            )

        user_data = enrollment_report_provider.get_user_profile(student.id)
        course_enrollment_data = enrollment_report_provider.get_enrollment_info(student, course_id)
        payment_data = enrollment_report_provider.get_payment_info(student, course_id)

        # display name map for the column headers
        enrollment_report_headers = {
            'User ID': _('User ID'),
            'Username': _('Username'),
            'Full Name': _('Full Name'),
            'First Name': _('First Name'),
            'Last Name': _('Last Name'),
            'Company Name': _('Company Name'),
            'Title': _('Title'),
            'Language': _('Language'),
            'Year of Birth': _('Year of Birth'),
            'Gender': _('Gender'),
            'Level of Education': _('Level of Education'),
            'Mailing Address': _('Mailing Address'),
            'Goals': _('Goals'),
            'City': _('City'),
            'Country': _('Country'),
            'Enrollment Date': _('Enrollment Date'),
            'Currently Enrolled': _('Currently Enrolled'),
            'Enrollment Source': _('Enrollment Source'),
            'Manual (Un)Enrollment Reason': _('Manual (Un)Enrollment Reason'),
            'Enrollment Role': _('Enrollment Role'),
            'List Price': _('List Price'),
            'Payment Amount': _('Payment Amount'),
            'Coupon Codes Used': _('Coupon Codes Used'),
            'Registration Code Used': _('Registration Code Used'),
            'Payment Status': _('Payment Status'),
            'Transaction Reference Number': _('Transaction Reference Number')
        }

        if not header:
            header = user_data.keys() + course_enrollment_data.keys() + payment_data.keys()
            display_headers = []
            for header_element in header:
                # translate header into a localizable display string
                display_headers.append(enrollment_report_headers.get(header_element, header_element))
            rows.append(display_headers)

        rows.append(user_data.values() + course_enrollment_data.values() + payment_data.values())
        task_progress.succeeded += 1

    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, Detailed enrollment report generated for students: %s/%s',
        task_info_string,
        action_name,
        current_step,
        student_counter,
        total_students
    )

    # By this point, we've got the rows we're going to stuff into our CSV files.
    current_step = {'step': 'Uploading CSVs'}
    task_progress.update_task_state(extra_meta=current_step)
    TASK_LOG.info(u'%s, Task type: %s, Current step: %s', task_info_string, action_name, current_step)

    # Perform the actual upload
    upload_csv_to_report_store(rows, 'enrollment_report', course_id, start_date, config_name='FINANCIAL_REPORTS')

    # One last update before we close out...
    TASK_LOG.info(u'%s, Task type: %s, Finalizing detailed enrollment task', task_info_string, action_name)
    return task_progress.update_task_state(extra_meta=current_step)


def upload_may_enroll_csv(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate a CSV file containing
    information about students who may enroll but have not done so
    yet, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about students who may enroll'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = task_input.get('features')
    student_data = list_may_enroll(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'may_enroll_info', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def get_executive_report(course_id):
    """
    Returns dict containing information about the course executive summary.
    """
    single_purchase_total = PaidCourseRegistration.get_total_amount_of_purchased_item(course_id)
    bulk_purchase_total = CourseRegCodeItem.get_total_amount_of_purchased_item(course_id)
    paid_invoices_total = InvoiceTransaction.get_total_amount_of_paid_course_invoices(course_id)
    gross_paid_revenue = single_purchase_total + bulk_purchase_total + paid_invoices_total

    all_invoices_total = Invoice.get_invoice_total_amount_for_course(course_id)
    gross_pending_revenue = all_invoices_total - float(paid_invoices_total)

    gross_revenue = float(gross_paid_revenue) + float(gross_pending_revenue)

    refunded_self_purchased_seats = PaidCourseRegistration.get_self_purchased_seat_count(
        course_id, status='refunded'
    )
    refunded_bulk_purchased_seats = CourseRegCodeItem.get_bulk_purchased_seat_count(
        course_id, status='refunded'
    )
    total_seats_refunded = refunded_self_purchased_seats + refunded_bulk_purchased_seats

    self_purchased_refunds = PaidCourseRegistration.get_total_amount_of_purchased_item(
        course_id,
        status='refunded'
    )
    bulk_purchase_refunds = CourseRegCodeItem.get_total_amount_of_purchased_item(course_id, status='refunded')
    total_amount_refunded = self_purchased_refunds + bulk_purchase_refunds

    top_discounted_codes = CouponRedemption.get_top_discount_codes_used(course_id)
    total_coupon_codes_purchases = CouponRedemption.get_total_coupon_code_purchases(course_id)

    bulk_purchased_codes = CourseRegistrationCode.order_generated_registration_codes(course_id)

    unused_registration_codes = 0
    for registration_code in bulk_purchased_codes:
        if not RegistrationCodeRedemption.is_registration_code_redeemed(registration_code.code):
            unused_registration_codes += 1

    self_purchased_seat_count = PaidCourseRegistration.get_self_purchased_seat_count(course_id)
    bulk_purchased_seat_count = CourseRegCodeItem.get_bulk_purchased_seat_count(course_id)
    total_invoiced_seats = CourseRegistrationCode.invoice_generated_registration_codes(course_id).count()

    total_seats = self_purchased_seat_count + bulk_purchased_seat_count + total_invoiced_seats

    self_purchases_percentage = 0.0
    bulk_purchases_percentage = 0.0
    invoice_purchases_percentage = 0.0
    avg_price_paid = 0.0

    if total_seats != 0:
        self_purchases_percentage = (float(self_purchased_seat_count) / float(total_seats)) * 100
        bulk_purchases_percentage = (float(bulk_purchased_seat_count) / float(total_seats)) * 100
        invoice_purchases_percentage = (float(total_invoiced_seats) / float(total_seats)) * 100
        avg_price_paid = gross_revenue / total_seats

    course = get_course_by_id(course_id, depth=0)
    currency = settings.PAID_COURSE_REGISTRATION_CURRENCY[1]

    return {
        'display_name': course.display_name,
        'start_date': course.start.strftime("%Y-%m-%d") if course.start is not None else 'N/A',
        'end_date': course.end.strftime("%Y-%m-%d") if course.end is not None else 'N/A',
        'total_seats': total_seats,
        'currency': currency,
        'gross_revenue': float(gross_revenue),
        'gross_paid_revenue': float(gross_paid_revenue),
        'gross_pending_revenue': gross_pending_revenue,
        'total_seats_refunded': total_seats_refunded,
        'total_amount_refunded': float(total_amount_refunded),
        'average_paid_price': float(avg_price_paid),
        'discount_codes_data': top_discounted_codes,
        'total_seats_using_discount_codes': total_coupon_codes_purchases,
        'total_self_purchase_seats': self_purchased_seat_count,
        'total_bulk_purchase_seats': bulk_purchased_seat_count,
        'total_invoiced_seats': total_invoiced_seats,
        'unused_bulk_purchase_code_count': unused_registration_codes,
        'self_purchases_percentage': self_purchases_percentage,
        'bulk_purchases_percentage': bulk_purchases_percentage,
        'invoice_purchases_percentage': invoice_purchases_percentage,
    }


def upload_exec_summary_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a html report containing information,
    which provides a snapshot of how the course is doing.
    """
    start_time = time()
    report_generation_date = datetime.now(UTC)
    status_interval = 100

    enrolled_users = CourseEnrollment.objects.users_enrolled_in(course_id)
    true_enrollment_count = 0
    for user in enrolled_users:
        if not user.is_staff and not CourseAccessRole.objects.filter(
                user=user, course_id=course_id, role__in=FILTERED_OUT_ROLES
        ).exists():
            true_enrollment_count += 1

    task_progress = TaskProgress(action_name, true_enrollment_count, start_time)

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )

    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)
    current_step = {'step': 'Gathering executive summary report information'}

    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s, generating executive summary report',
        task_info_string,
        action_name,
        current_step
    )

    if task_progress.attempted % status_interval == 0:
        task_progress.update_task_state(extra_meta=current_step)
    task_progress.attempted += 1

    # get the course executive summary report information.
    data_dict = get_executive_report(course_id)
    data_dict.update(
        {
            'total_enrollments': true_enrollment_count,
            'report_generation_date': report_generation_date.strftime("%Y-%m-%d"),
        }
    )

    # By this point, we've got the data that we need to generate html report.
    current_step = {'step': 'Uploading executive summary report HTML file'}
    task_progress.update_task_state(extra_meta=current_step)
    TASK_LOG.info(u'%s, Task type: %s, Current step: %s', task_info_string, action_name, current_step)

    # Perform the actual upload
    upload_exec_summary_to_store(data_dict, 'executive_report', course_id, report_generation_date)
    task_progress.succeeded += 1
    # One last update before we close out...
    TASK_LOG.info(u'%s, Task type: %s, Finalizing executive summary report task', task_info_string, action_name)
    return task_progress.update_task_state(extra_meta=current_step)


def upload_course_survey_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):
    """
    For a given `course_id`, generate a html report containing the survey results for a course.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)

    current_step = {'step': 'Gathering course survey report information'}
    task_progress.update_task_state(extra_meta=current_step)

    distinct_survey_fields_queryset = SurveyAnswer.objects.filter(course_key=course_id).values('field_name').distinct()
    survey_fields = []
    for unique_field_row in distinct_survey_fields_queryset:
        survey_fields.append(unique_field_row['field_name'])
    survey_fields.sort()

    user_survey_answers = OrderedDict()
    survey_answers_for_course = SurveyAnswer.objects.filter(course_key=course_id).select_related('user')

    for survey_field_record in survey_answers_for_course:
        user_id = survey_field_record.user.id
        if user_id not in user_survey_answers.keys():
            user_survey_answers[user_id] = {
                'username': survey_field_record.user.username,
                'email': survey_field_record.user.email
            }

        user_survey_answers[user_id][survey_field_record.field_name] = survey_field_record.field_value

    header = ["User ID", "User Name", "Email"]
    header.extend(survey_fields)
    csv_rows = []

    for user_id in user_survey_answers.keys():
        row = []
        row.append(user_id)
        row.append(user_survey_answers[user_id].get('username', ''))
        row.append(user_survey_answers[user_id].get('email', ''))
        for survey_field in survey_fields:
            row.append(user_survey_answers[user_id].get(survey_field, ''))
        csv_rows.append(row)

    task_progress.attempted = task_progress.succeeded = len(csv_rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    csv_rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(csv_rows, 'course_survey_results', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def upload_proctored_exam_results_report(_xmodule_instance_args, _entry_id, course_id, _task_input, action_name):  # pylint: disable=invalid-name
    """
    For a given `course_id`, generate a CSV file containing
    information about proctored exam results, and store using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)
    num_reports = 1
    task_progress = TaskProgress(action_name, num_reports, start_time)
    current_step = {'step': 'Calculating info about proctored exam results in a course'}
    task_progress.update_task_state(extra_meta=current_step)

    # Compute result table and format it
    query_features = _task_input.get('features')
    student_data = get_proctored_exam_results(course_id, query_features)
    header, rows = format_dictlist(student_data, query_features)

    task_progress.attempted = task_progress.succeeded = len(rows)
    task_progress.skipped = task_progress.total - task_progress.attempted

    rows.insert(0, header)

    current_step = {'step': 'Uploading CSV'}
    task_progress.update_task_state(extra_meta=current_step)

    # Perform the upload
    upload_csv_to_report_store(rows, 'proctored_exam_results_report', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def generate_students_certificates(
        _xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    For a given `course_id`, generate certificates for only students present in 'students' key in task_input
    json column, otherwise generate certificates for all enrolled students.
    """
    start_time = time()
    students_to_generate_certs_for = CourseEnrollment.objects.users_enrolled_in(course_id)

    student_set = task_input.get('student_set')
    if student_set == 'all_whitelisted':
        # Generate Certificates for all white listed students.
        students_to_generate_certs_for = students_to_generate_certs_for.filter(
            certificatewhitelist__course_id=course_id,
            certificatewhitelist__whitelist=True
        )

    elif student_set == 'whitelisted_not_generated':
        # Whitelist students who did not get certificates already.
        students_to_generate_certs_for = students_to_generate_certs_for.filter(
            certificatewhitelist__course_id=course_id,
            certificatewhitelist__whitelist=True
        ).exclude(
            generatedcertificate__course_id=course_id,
            generatedcertificate__status__in=CertificateStatuses.PASSED_STATUSES
        )

    elif student_set == "specific_student":
        specific_student_id = task_input.get('specific_student_id')
        students_to_generate_certs_for = students_to_generate_certs_for.filter(id=specific_student_id)

    task_progress = TaskProgress(action_name, students_to_generate_certs_for.count(), start_time)

    current_step = {'step': 'Calculating students already have certificates'}
    task_progress.update_task_state(extra_meta=current_step)

    statuses_to_regenerate = task_input.get('statuses_to_regenerate', [])
    if student_set is not None and not statuses_to_regenerate:
        # We want to skip 'filtering students' only when students are given and statuses to regenerate are not
        students_require_certs = students_to_generate_certs_for
    else:
        students_require_certs = students_require_certificate(
            course_id, students_to_generate_certs_for, statuses_to_regenerate
        )

    if statuses_to_regenerate:
        # Mark existing generated certificates as 'unavailable' before regenerating
        # We need to call this method after "students_require_certificate" otherwise "students_require_certificate"
        # would return no results.
        invalidate_generated_certificates(course_id, students_to_generate_certs_for, statuses_to_regenerate)

    task_progress.skipped = task_progress.total - len(students_require_certs)

    current_step = {'step': 'Generating Certificates'}
    task_progress.update_task_state(extra_meta=current_step)

    course = modulestore().get_course(course_id, depth=0)
    # Generate certificate for each student
    for student in students_require_certs:
        task_progress.attempted += 1
        status = generate_user_certificates(
            student,
            course_id,
            course=course
        )

        if CertificateStatuses.is_passing_status(status):
            task_progress.succeeded += 1
        else:
            task_progress.failed += 1

    return task_progress.update_task_state(extra_meta=current_step)


def cohort_students_and_upload(_xmodule_instance_args, _entry_id, course_id, task_input, action_name):
    """
    Within a given course, cohort students in bulk, then upload the results
    using a `ReportStore`.
    """
    start_time = time()
    start_date = datetime.now(UTC)

    # Iterate through rows to get total assignments for task progress
    with DefaultStorage().open(task_input['file_name']) as f:
        total_assignments = 0
        for _line in unicodecsv.DictReader(UniversalNewlineIterator(f)):
            total_assignments += 1

    task_progress = TaskProgress(action_name, total_assignments, start_time)
    current_step = {'step': 'Cohorting Students'}
    task_progress.update_task_state(extra_meta=current_step)

    # cohorts_status is a mapping from cohort_name to metadata about
    # that cohort.  The metadata will include information about users
    # successfully added to the cohort, users not found, and a cached
    # reference to the corresponding cohort object to prevent
    # redundant cohort queries.
    cohorts_status = {}

    with DefaultStorage().open(task_input['file_name']) as f:
        for row in unicodecsv.DictReader(UniversalNewlineIterator(f), encoding='utf-8'):
            # Try to use the 'email' field to identify the user.  If it's not present, use 'username'.
            username_or_email = row.get('email') or row.get('username')
            cohort_name = row.get('cohort') or ''
            task_progress.attempted += 1

            if not cohorts_status.get(cohort_name):
                cohorts_status[cohort_name] = {
                    'Cohort Name': cohort_name,
                    'Students Added': 0,
                    'Students Not Found': set()
                }
                try:
                    cohorts_status[cohort_name]['cohort'] = CourseUserGroup.objects.get(
                        course_id=course_id,
                        group_type=CourseUserGroup.COHORT,
                        name=cohort_name
                    )
                    cohorts_status[cohort_name]["Exists"] = True
                except CourseUserGroup.DoesNotExist:
                    cohorts_status[cohort_name]["Exists"] = False

            if not cohorts_status[cohort_name]['Exists']:
                task_progress.failed += 1
                continue

            try:
                add_user_to_cohort(cohorts_status[cohort_name]['cohort'], username_or_email)
                cohorts_status[cohort_name]['Students Added'] += 1
                task_progress.succeeded += 1
            except User.DoesNotExist:
                cohorts_status[cohort_name]['Students Not Found'].add(username_or_email)
                task_progress.failed += 1
            except ValueError:
                # Raised when the user is already in the given cohort
                task_progress.skipped += 1

            task_progress.update_task_state(extra_meta=current_step)

    current_step['step'] = 'Uploading CSV'
    task_progress.update_task_state(extra_meta=current_step)

    # Filter the output of `add_users_to_cohorts` in order to upload the result.
    output_header = ['Cohort Name', 'Exists', 'Students Added', 'Students Not Found']
    output_rows = [
        [
            ','.join(status_dict.get(column_name, '')) if column_name == 'Students Not Found'
            else status_dict[column_name]
            for column_name in output_header
        ]
        for _cohort_name, status_dict in cohorts_status.iteritems()
    ]
    output_rows.insert(0, output_header)
    upload_csv_to_report_store(output_rows, 'cohort_results', course_id, start_date)

    return task_progress.update_task_state(extra_meta=current_step)


def students_require_certificate(course_id, enrolled_students, statuses_to_regenerate=None):
    """
    Returns list of students where certificates needs to be generated.
    if 'statuses_to_regenerate' is given then return students that have Generated Certificates
    and the generated certificate status lies in 'statuses_to_regenerate'

    if 'statuses_to_regenerate' is not given then return all the enrolled student skipping the ones
    whose certificates have already been generated.

    :param course_id:
    :param enrolled_students:
    :param statuses_to_regenerate:
    """
    if statuses_to_regenerate:
        # Return Students that have Generated Certificates and the generated certificate status
        # lies in 'statuses_to_regenerate'
        students_require_certificates = enrolled_students.filter(
            generatedcertificate__course_id=course_id,
            generatedcertificate__status__in=statuses_to_regenerate
        )
        # Fetch results otherwise subsequent operations on table cause wrong data fetch
        return list(students_require_certificates)
    else:
        # compute those students whose certificates are already generated
        students_already_have_certs = User.objects.filter(
            ~Q(generatedcertificate__status=CertificateStatuses.unavailable),
            generatedcertificate__course_id=course_id)

        # Return all the enrolled student skipping the ones whose certificates have already been generated
        return list(set(enrolled_students) - set(students_already_have_certs))


def invalidate_generated_certificates(course_id, enrolled_students, certificate_statuses):  # pylint: disable=invalid-name
    """
    Invalidate generated certificates for all enrolled students in the given course having status in
    'certificate_statuses'.

    Generated Certificates are invalidated by marking its status 'unavailable' and updating verify_uuid, download_uuid,
    download_url and grade with empty string.

    :param course_id: Course Key for the course whose generated certificates need to be removed
    :param enrolled_students: (queryset or list) students enrolled in the course
    :param certificate_statuses: certificates statuses for whom to remove generated certificate
    """
    certificates = GeneratedCertificate.objects.filter(  # pylint: disable=no-member
        user__in=enrolled_students,
        course_id=course_id,
        status__in=certificate_statuses,
    )

    # Mark generated certificates as 'unavailable' and update download_url, download_uui, verify_uuid and
    # grade with empty string for each row
    certificates.update(
        status=CertificateStatuses.unavailable,
        verify_uuid='',
        download_uuid='',
        download_url='',
        grade='',
    )


def upload_ora2_data(
        _xmodule_instance_args, _entry_id, course_id, _task_input, action_name
):
    """
    Collect ora2 responses and upload them to S3 as a CSV
    """

    start_date = datetime.now(UTC)
    start_time = time()

    num_attempted = 1
    num_total = 1

    fmt = u'Task: {task_id}, InstructorTask ID: {entry_id}, Course: {course_id}, Input: {task_input}'
    task_info_string = fmt.format(
        task_id=_xmodule_instance_args.get('task_id') if _xmodule_instance_args is not None else None,
        entry_id=_entry_id,
        course_id=course_id,
        task_input=_task_input
    )
    TASK_LOG.info(u'%s, Task type: %s, Starting task execution', task_info_string, action_name)

    task_progress = TaskProgress(action_name, num_total, start_time)
    task_progress.attempted = num_attempted

    curr_step = {'step': "Collecting responses"}
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s for all submissions',
        task_info_string,
        action_name,
        curr_step,
    )

    task_progress.update_task_state(extra_meta=curr_step)

    try:
        header, datarows = OraAggregateData.collect_ora2_data(course_id)
        rows = [header] + [row for row in datarows]
    # Update progress to failed regardless of error type
    except Exception:  # pylint: disable=broad-except
        TASK_LOG.exception('Failed to get ORA data.')
        task_progress.failed = 1
        curr_step = {'step': "Error while collecting data"}

        task_progress.update_task_state(extra_meta=curr_step)

        return UPDATE_STATUS_FAILED

    task_progress.succeeded = 1
    curr_step = {'step': "Uploading CSV"}
    TASK_LOG.info(
        u'%s, Task type: %s, Current step: %s',
        task_info_string,
        action_name,
        curr_step,
    )
    task_progress.update_task_state(extra_meta=curr_step)

    upload_csv_to_report_store(rows, 'ORA_data', course_id, start_date)

    curr_step = {'step': 'Finalizing ORA data report'}
    task_progress.update_task_state(extra_meta=curr_step)
    TASK_LOG.info(u'%s, Task type: %s, Upload complete.', task_info_string, action_name)

    return UPDATE_STATUS_SUCCEEDED
