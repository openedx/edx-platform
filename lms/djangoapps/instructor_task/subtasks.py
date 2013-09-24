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


def create_subtask_result(new_num_sent, new_num_error, new_num_optout):
    """Return the result of course_email sending as a dict (not a string)."""
    attempted = new_num_sent + new_num_error
    current_result = {'attempted': attempted, 'succeeded': new_num_sent, 'skipped': new_num_optout, 'failed': new_num_error}
    return current_result


def update_instructor_task_for_subtasks(entry, action_name, total_num, subtask_id_list):
    """
    Store initial subtask information to InstructorTask object.

    # Before we actually start running the tasks we've defined,
    # the InstructorTask needs to be updated with their information.
    # So we update the InstructorTask object here, not in the return.
    # The monitoring code knows that it shouldn't go to the InstructorTask's task's
    # Result for its progress when there are subtasks.  So we accumulate
    # the results of each subtask as it completes into the InstructorTask.
    # At this point, we have some status that we can report, as to the magnitude of the overall
    # task.  That is, we know the total.  Set that, and our subtasks should work towards that goal.
    # Note that we add start_time in here, so that it can be used
    # by subtasks to calculate duration_ms values:
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
