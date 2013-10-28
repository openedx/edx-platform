"""
This module contains celery task functions for handling the management of subtasks.
"""
from time import time
import json

from celery.utils.log import get_task_logger
from celery.states import SUCCESS, READY_STATES, RETRY

from django.db import transaction
from django.core.cache import cache

from instructor_task.models import InstructorTask, PROGRESS, QUEUING

TASK_LOG = get_task_logger(__name__)

# Lock expiration should be long enough to allow a send_course_email task to complete.
SUBTASK_LOCK_EXPIRE = 60 * 10  # Lock expires in 10 minutes


class DuplicateTaskException(Exception):
    """Exception indicating that a task already exists or has already completed."""
    pass


def create_subtask_status(task_id, succeeded=0, failed=0, skipped=0, retried_nomax=0, retried_withmax=0, state=None):
    """
    Create and return a dict for tracking the status of a subtask.

    Subtask status keys are:

      'task_id' : id of subtask.  This is used to pass task information across retries.
      'attempted' : number of attempts -- should equal succeeded plus failed
      'succeeded' : number that succeeded in processing
      'skipped' : number that were not processed.
      'failed' : number that failed during processing
      'retried_nomax' : number of times the subtask has been retried for conditions that
          should not have a maximum count applied
      'retried_withmax' : number of times the subtask has been retried for conditions that
          should have a maximum count applied
      'state' : celery state of the subtask (e.g. QUEUING, PROGRESS, RETRY, FAILURE, SUCCESS)

    Object must be JSON-serializable, so that it can be passed as an argument
    to tasks.

    In future, we may want to include specific error information
    indicating the reason for failure.
    Also, we should count up "not attempted" separately from attempted/failed.
    """
    attempted = succeeded + failed
    current_result = {
        'task_id': task_id,
        'attempted': attempted,
        'succeeded': succeeded,
        'skipped': skipped,
        'failed': failed,
        'retried_nomax': retried_nomax,
        'retried_withmax': retried_withmax,
        'state': state if state is not None else QUEUING,
    }
    return current_result


def increment_subtask_status(subtask_result, succeeded=0, failed=0, skipped=0, retried_nomax=0, retried_withmax=0, state=None):
    """
    Update the result of a subtask with additional results.

    Create and return a dict for tracking the status of a subtask.

    Keys for input `subtask_result` and returned subtask_status are:

      'task_id' : id of subtask.  This is used to pass task information across retries.
      'attempted' : number of attempts -- should equal succeeded plus failed
      'succeeded' : number that succeeded in processing
      'skipped' : number that were not processed.
      'failed' : number that failed during processing
      'retried_nomax' : number of times the subtask has been retried for conditions that
          should not have a maximum count applied
      'retried_withmax' : number of times the subtask has been retried for conditions that
          should have a maximum count applied
      'state' : celery state of the subtask (e.g. QUEUING, PROGRESS, RETRY, FAILURE, SUCCESS)

    Kwarg arguments are incremented to the corresponding key in `subtask_result`.
    The exception is for `state`, which if specified is used to override the existing value.
    """
    new_result = dict(subtask_result)
    new_result['attempted'] += (succeeded + failed)
    new_result['succeeded'] += succeeded
    new_result['failed'] += failed
    new_result['skipped'] += skipped
    new_result['retried_nomax'] += retried_nomax
    new_result['retried_withmax'] += retried_withmax
    if state is not None:
        new_result['state'] = state

    return new_result


def _get_retry_count(subtask_status):
    """
    Calculate the total number of retries.
    """
    count = 0
    for keyname in ['retried_nomax', 'retried_withmax']:
        count += subtask_status.get(keyname, 0)
    return count


def initialize_subtask_info(entry, action_name, total_num, subtask_id_list):
    """
    Store initial subtask information to InstructorTask object.

    The InstructorTask's "task_output" field is initialized.  This is a JSON-serialized dict.
    Counters for 'attempted', 'succeeded', 'failed', 'skipped' keys are initialized to zero,
    as is the 'duration_ms' value.  A 'start_time' is stored for later duration calculations,
    and the total number of "things to do" is set, so the user can be told how much needs to be
    done overall.  The `action_name` is also stored, to help with constructing more readable
    task_progress messages.

    The InstructorTask's "subtasks" field is also initialized.  This is also a JSON-serialized dict.
    Keys include 'total', 'succeeded', 'retried', 'failed', which are counters for the number of
    subtasks.  'Total' is set here to the total number, while the other three are initialized to zero.
    Once the counters for 'succeeded' and 'failed' match the 'total', the subtasks are done and
    the InstructorTask's "status" will be changed to SUCCESS.

    The "subtasks" field also contains a 'status' key, that contains a dict that stores status
    information for each subtask.  The value for each subtask (keyed by its task_id)
    is its subtask status, as defined by create_subtask_status().

    This information needs to be set up in the InstructorTask before any of the subtasks start
    running.  If not, there is a chance that the subtasks could complete before the parent task
    is done creating subtasks.  Doing so also simplifies the save() here, as it avoids the need
    for locking.

    Monitoring code should assume that if an InstructorTask has subtask information, that it should
    rely on the status stored in the InstructorTask object, rather than status stored in the
    corresponding AsyncResult.
    """
    task_progress = {
        'action_name': action_name,
        'attempted': 0,
        'failed': 0,
        'skipped': 0,
        'succeeded': 0,
        'total': total_num,
        'duration_ms': int(0),
        'start_time': time()
    }
    entry.task_output = InstructorTask.create_output_for_success(task_progress)
    entry.task_state = PROGRESS

    # Write out the subtasks information.
    num_subtasks = len(subtask_id_list)
    # Note that may not be necessary to store initial value with all those zeroes!
    subtask_status = {subtask_id: create_subtask_status(subtask_id) for subtask_id in subtask_id_list}
    subtask_dict = {
        'total': num_subtasks,
        'succeeded': 0,
        'failed': 0,
        'status': subtask_status
    }
    entry.subtasks = json.dumps(subtask_dict)

    # and save the entry immediately, before any subtasks actually start work:
    entry.save_now()
    return task_progress


def _acquire_subtask_lock(task_id):
    """
    Mark the specified task_id as being in progress.

    This is used to make sure that the same task is not worked on by more than one worker
    at the same time.  This can occur when tasks are requeued by Celery in response to
    loss of connection to the task broker.  Most of the time, such duplicate tasks are
    run sequentially, but they can overlap in processing as well.

    Returns true if the task_id was not already locked; false if it was.
    """
    # cache.add fails if the key already exists
    key = "subtask-{}".format(task_id)
    succeeded = cache.add(key, 'true', SUBTASK_LOCK_EXPIRE)
    if not succeeded:
        TASK_LOG.warning("task_id '%s': already locked.  Contains value '%s'", task_id, cache.get(key))
    return succeeded


def _release_subtask_lock(task_id):
    """
    Unmark the specified task_id as being no longer in progress.

    This is most important to permit a task to be retried.
    """
    # According to Celery task cookbook, "Memcache delete is very slow, but we have
    # to use it to take advantage of using add() for atomic locking."
    key = "subtask-{}".format(task_id)
    cache.delete(key)


def check_subtask_is_valid(entry_id, current_task_id, new_subtask_status):
    """
    Confirms that the current subtask is known to the InstructorTask and hasn't already been completed.

    Problems can occur when the parent task has been run twice, and results in duplicate
    subtasks being created for the same InstructorTask entry.  This can happen when Celery
    loses its connection to its broker, and any current tasks get requeued.

    If a parent task gets requeued, then the same InstructorTask may have a different set of
    subtasks defined (to do the same thing), so the subtasks from the first queuing would not
    be known to the InstructorTask.  We return an exception in this case.

    If a subtask gets requeued, then the first time the subtask runs it should run fine to completion.
    However, we want to prevent it from running again, so we check here to see what the existing
    subtask's status is.  If it is complete, we raise an exception.  We also take a lock on the task,
    so that we can detect if another worker has started work but has not yet completed that work.
    The other worker is allowed to finish, and this raises an exception.

    Raises a DuplicateTaskException exception if it's not a task that should be run.
    """
    # Confirm that the InstructorTask actually defines subtasks.
    entry = InstructorTask.objects.get(pk=entry_id)
    if len(entry.subtasks) == 0:
        format_str = "Unexpected task_id '{}': unable to find subtasks of instructor task '{}': rejecting task {}"
        msg = format_str.format(current_task_id, entry, new_subtask_status)
        TASK_LOG.warning(msg)
        raise DuplicateTaskException(msg)

    # Confirm that the InstructorTask knows about this particular subtask.
    subtask_dict = json.loads(entry.subtasks)
    subtask_status_info = subtask_dict['status']
    if current_task_id not in subtask_status_info:
        format_str = "Unexpected task_id '{}': unable to find status for subtask of instructor task '{}': rejecting task {}"
        msg = format_str.format(current_task_id, entry, new_subtask_status)
        TASK_LOG.warning(msg)
        raise DuplicateTaskException(msg)

    # Confirm that the InstructorTask doesn't think that this subtask has already been
    # performed successfully.
    subtask_status = subtask_status_info[current_task_id]
    subtask_state = subtask_status.get('state')
    if subtask_state in READY_STATES:
        format_str = "Unexpected task_id '{}': already completed - status {} for subtask of instructor task '{}': rejecting task {}"
        msg = format_str.format(current_task_id, subtask_status, entry, new_subtask_status)
        TASK_LOG.warning(msg)
        raise DuplicateTaskException(msg)

    # Confirm that the InstructorTask doesn't think that this subtask is already being
    # retried by another task.
    if subtask_state == RETRY:
        # Check to see if the input number of retries is less than the recorded number.
        # If so, then this is an earlier version of the task, and a duplicate.
        new_retry_count = _get_retry_count(new_subtask_status)
        current_retry_count = _get_retry_count(subtask_status)
        if new_retry_count < current_retry_count:
            format_str = "Unexpected task_id '{}': already retried - status {} for subtask of instructor task '{}': rejecting task {}"
            msg = format_str.format(current_task_id, subtask_status, entry, new_subtask_status)
            TASK_LOG.warning(msg)
            raise DuplicateTaskException(msg)

    # Now we are ready to start working on this.  Try to lock it.
    # If it fails, then it means that another worker is already in the
    # middle of working on this.
    if not _acquire_subtask_lock(current_task_id):
        format_str = "Unexpected task_id '{}': already being executed - for subtask of instructor task '{}'"
        msg = format_str.format(current_task_id, entry)
        TASK_LOG.warning(msg)
        raise DuplicateTaskException(msg)


@transaction.commit_manually
def update_subtask_status(entry_id, current_task_id, new_subtask_status):
    """
    Update the status of the subtask in the parent InstructorTask object tracking its progress.

    Uses select_for_update to lock the InstructorTask object while it is being updated.
    The operation is surrounded by a try/except/else that permit the manual transaction to be
    committed on completion, or rolled back on error.

    The InstructorTask's "task_output" field is updated.  This is a JSON-serialized dict.
    Accumulates values for 'attempted', 'succeeded', 'failed', 'skipped' from `new_subtask_status`
    into the corresponding values in the InstructorTask's task_output.  Also updates the 'duration_ms'
    value with the current interval since the original InstructorTask started.  Note that this
    value is only approximate, since the subtask may be running on a different server than the
    original task, so is subject to clock skew.

    The InstructorTask's "subtasks" field is also updated.  This is also a JSON-serialized dict.
    Keys include 'total', 'succeeded', 'retried', 'failed', which are counters for the number of
    subtasks.  'Total' is expected to have been set at the time the subtasks were created.
    The other three counters are incremented depending on the value of `status`.  Once the counters
    for 'succeeded' and 'failed' match the 'total', the subtasks are done and the InstructorTask's
    "status" is changed to SUCCESS.

    The "subtasks" field also contains a 'status' key, that contains a dict that stores status
    information for each subtask.  At the moment, the value for each subtask (keyed by its task_id)
    is the value of `status`, but could be expanded in future to store information about failure
    messages, progress made, etc.
    """
    TASK_LOG.info("Preparing to update status for email subtask %s for instructor task %d with status %s",
                  current_task_id, entry_id, new_subtask_status)

    try:
        entry = InstructorTask.objects.select_for_update().get(pk=entry_id)
        subtask_dict = json.loads(entry.subtasks)
        subtask_status_info = subtask_dict['status']
        if current_task_id not in subtask_status_info:
            # unexpected error -- raise an exception
            format_str = "Unexpected task_id '{}': unable to update status for email subtask of instructor task '{}'"
            msg = format_str.format(current_task_id, entry_id)
            TASK_LOG.warning(msg)
            raise ValueError(msg)

        # Update status:
        subtask_status_info[current_task_id] = new_subtask_status

        # Update the parent task progress.
        # Set the estimate of duration, but only if it
        # increases.  Clock skew between time() returned by different machines
        # may result in non-monotonic values for duration.
        task_progress = json.loads(entry.task_output)
        start_time = task_progress['start_time']
        prev_duration = task_progress['duration_ms']
        new_duration = int((time() - start_time) * 1000)
        task_progress['duration_ms'] = max(prev_duration, new_duration)

        # Update counts only when subtask is done.
        # In future, we can make this more responsive by updating status
        # between retries, by comparing counts that change from previous
        # retry.
        new_state = new_subtask_status['state']
        if new_subtask_status is not None and new_state in READY_STATES:
            for statname in ['attempted', 'succeeded', 'failed', 'skipped']:
                task_progress[statname] += new_subtask_status[statname]

        # Figure out if we're actually done (i.e. this is the last task to complete).
        # This is easier if we just maintain a counter, rather than scanning the
        # entire new_subtask_status dict.
        if new_state == SUCCESS:
            subtask_dict['succeeded'] += 1
        elif new_state in READY_STATES:
            subtask_dict['failed'] += 1
        num_remaining = subtask_dict['total'] - subtask_dict['succeeded'] - subtask_dict['failed']

        # If we're done with the last task, update the parent status to indicate that.
        # At present, we mark the task as having succeeded.  In future, we should see
        # if there was a catastrophic failure that occurred, and figure out how to
        # report that here.
        if num_remaining <= 0:
            entry.task_state = SUCCESS
        entry.subtasks = json.dumps(subtask_dict)
        entry.task_output = InstructorTask.create_output_for_success(task_progress)

        TASK_LOG.info("Task output updated to %s for email subtask %s of instructor task %d",
                      entry.task_output, current_task_id, entry_id)
        TASK_LOG.debug("about to save....")
        entry.save()
    except Exception:
        TASK_LOG.exception("Unexpected error while updating InstructorTask.")
        transaction.rollback()
        raise
    else:
        TASK_LOG.debug("about to commit....")
        transaction.commit()
    finally:
        _release_subtask_lock(current_task_id)
