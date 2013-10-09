"""
This module contains celery task functions for handling the management of subtasks.
"""
from time import time
import json

from celery.utils.log import get_task_logger
from celery.states import SUCCESS, READY_STATES

from django.db import transaction

from instructor_task.models import InstructorTask, PROGRESS, QUEUING

TASK_LOG = get_task_logger(__name__)


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
