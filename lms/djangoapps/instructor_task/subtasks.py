"""
This module contains celery task functions for handling the management of subtasks.
"""
from time import time
import json

from celery.utils.log import get_task_logger
from celery.states import SUCCESS, RETRY

from django.db import transaction

from instructor_task.models import InstructorTask, PROGRESS, QUEUING

TASK_LOG = get_task_logger(__name__)


def create_subtask_result(num_sent, num_error, num_optout):
    """
    Create a result of a subtask.

    Keys are:  'attempted', 'succeeded', 'skipped', 'failed'.

    Object must be JSON-serializable.
    """
    attempted = num_sent + num_error
    current_result = {'attempted': attempted, 'succeeded': num_sent, 'skipped': num_optout, 'failed': num_error}
    return current_result


def increment_subtask_result(subtask_result, new_num_sent, new_num_error, new_num_optout):
    """
    Update the result of a subtask with additional results.

    Keys are:  'attempted', 'succeeded', 'skipped', 'failed'.
    """
    new_result = create_subtask_result(new_num_sent, new_num_error, new_num_optout)
    for keyname in new_result:
        if keyname in subtask_result:
            new_result[keyname] += subtask_result[keyname]
    return new_result


def update_instructor_task_for_subtasks(entry, action_name, total_num, subtask_id_list):
    """
    Store initial subtask information to InstructorTask object.

    The InstructorTask's "task_output" field is initialized.  This is a JSON-serialized dict.
    Counters for 'attempted', 'succeeded', 'failed', 'skipped' keys are initialized to zero,
    as is the 'duration_ms' value.  A 'start_time' is stored for later duration calculations,
    and the total number of "things to do" is set, so the user can be told how much needs to be
    done overall.  The `action_name` is also stored, to also help with constructing more readable
    progress messages.

    The InstructorTask's "subtasks" field is also initialized.  This is also a JSON-serialized dict.
    Keys include 'total', 'succeeded', 'retried', 'failed', which are counters for the number of
    subtasks.  'Total' is set here to the total number, while the other three are initialized to zero.
    Once the counters for 'succeeded' and 'failed' match the 'total', the subtasks are done and
    the InstructorTask's "status" will be changed to SUCCESS.

    The "subtasks" field also contains a 'status' key, that contains a dict that stores status
    information for each subtask.  At the moment, the value for each subtask (keyed by its task_id)
    is the value of `status`, which is initialized here to QUEUING.

    This information needs to be set up in the InstructorTask before any of the subtasks start
    running.  If not, there is a chance that the subtasks could complete before the parent task
    is done creating subtasks.  Doing so also simplifies the save() here, as it avoids the need
    for locking.

    Monitoring code should assume that if an InstructorTask has subtask information, that it should
    rely on the status stored in the InstructorTask object, rather than status stored in the
    corresponding AsyncResult.
    """
    progress = {
        'action_name': action_name,
        'attempted': 0,
        'failed': 0,
        'skipped': 0,
        'succeeded': 0,
        'total': total_num,
        'duration_ms': int(0),
        'start_time': time()
    }
    entry.task_output = InstructorTask.create_output_for_success(progress)
    entry.task_state = PROGRESS

    # Write out the subtasks information.
    num_subtasks = len(subtask_id_list)
    subtask_status = dict.fromkeys(subtask_id_list, QUEUING)
    subtask_dict = {'total': num_subtasks, 'succeeded': 0, 'failed': 0, 'retried': 0, 'status': subtask_status}
    entry.subtasks = json.dumps(subtask_dict)

    # and save the entry immediately, before any subtasks actually start work:
    entry.save_now()
    return progress


@transaction.commit_manually
def update_subtask_status(entry_id, current_task_id, status, subtask_result):
    """
    Update the status of the subtask in the parent InstructorTask object tracking its progress.

    Uses select_for_update to lock the InstructorTask object while it is being updated.
    The operation is surrounded by a try/except/else that permit the manual transaction to be
    committed on completion, or rolled back on error.

    The InstructorTask's "task_output" field is updated.  This is a JSON-serialized dict.
    Accumulates values for 'attempted', 'succeeded', 'failed', 'skipped' from `subtask_result`
    into the corresponding values in the InstructorTask's task_output.  Also updates the 'duration_ms'
    value with the current interval since the original InstructorTask started.

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
                  current_task_id, entry_id, subtask_result)

    try:
        entry = InstructorTask.objects.select_for_update().get(pk=entry_id)
        subtask_dict = json.loads(entry.subtasks)
        subtask_status = subtask_dict['status']
        if current_task_id not in subtask_status:
            # unexpected error -- raise an exception
            format_str = "Unexpected task_id '{}': unable to update status for email subtask of instructor task '{}'"
            msg = format_str.format(current_task_id, entry_id)
            TASK_LOG.warning(msg)
            raise ValueError(msg)

        # Update status unless it has already been set.  This can happen
        # when a task is retried and running in eager mode -- the retries
        # will be updating before the original call, and we don't want their
        # ultimate status to be clobbered by the "earlier" updates.  This
        # should not be a problem in normal (non-eager) processing.
        old_status = subtask_status[current_task_id]
        if status != RETRY or old_status == QUEUING:
            subtask_status[current_task_id] = status

        # Update the parent task progress
        task_progress = json.loads(entry.task_output)
        start_time = task_progress['start_time']
        task_progress['duration_ms'] = int((time() - start_time) * 1000)
        if subtask_result is not None:
            for statname in ['attempted', 'succeeded', 'failed', 'skipped']:
                task_progress[statname] += subtask_result[statname]

        # Figure out if we're actually done (i.e. this is the last task to complete).
        # This is easier if we just maintain a counter, rather than scanning the
        # entire subtask_status dict.
        if status == SUCCESS:
            subtask_dict['succeeded'] += 1
        elif status == RETRY:
            subtask_dict['retried'] += 1
        else:
            subtask_dict['failed'] += 1
        num_remaining = subtask_dict['total'] - subtask_dict['succeeded'] - subtask_dict['failed']
        # If we're done with the last task, update the parent status to indicate that:
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
    else:
        TASK_LOG.debug("about to commit....")
        transaction.commit()
